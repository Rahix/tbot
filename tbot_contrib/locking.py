""" Machine Locking implementations for tbot """

import abc
import contextlib
import typing

import tbot
import tbot.tc.shell
from tbot.machine import linux, machine


class LockManagerBase(abc.ABC):
    """
    Defines the "interface" that each locking implementation needs to
    implement.
    """

    @abc.abstractmethod
    def request_machine_lock(
        self, name: str, *, expiry: typing.Optional[int] = None
    ) -> bool:
        """
        Request lock for machine named ``name``.

        This method will usually be called via the
        :py:class:`~tbot_contrib.locking.MachineLock` mixin.

        :param str name: Name of the lock to be acquired.
        :param int expiry: Optional timeout after which a lock should 'expire'.
            When a lock is expired, followup locking requests will treat it as
            unlocked.  This can be used as a safeguard if a testcase fails
            without unlocking.
        :returns: ``True`` if the lock has been acquired successfully and
            ``False`` otherwise.
        """
        raise tbot.error.AbstractMethodError()

    @abc.abstractmethod
    def release_machine_lock(self, name: str) -> None:
        """
        Release lock for machine named ``name``.
        """
        raise tbot.error.AbstractMethodError()


class MachineLock(machine.PreConnectInitializer):
    """
    This is the initializer that is inherited by the board machine.  It just
    calls the lab-host's locking implementation.
    """

    lock_expiry: typing.Optional[int] = None
    """
    Timeout after which the lock should be considered expired.

    This provides a safeguard in case a testcase crashes without unlocking
    a lock - After the lock has expired, it will be considered unlocked again
    and a new testcase can acquire it.
    """

    @property
    def lock_name(self) -> str:
        """
        Prefix from which lock file name is derived.

        Defaults to the machine's name: ``self.name``.
        """
        return self.name

    @contextlib.contextmanager
    def _init_pre_connect(self) -> typing.Iterator:
        with tbot.ctx.request(tbot.role.LabHost) as labhost:
            if not isinstance(labhost, LockManagerBase):
                raise Exception("selected lab-host is not a lock manager")
            if not labhost.request_machine_lock(
                self.lock_name, expiry=self.lock_expiry
            ):
                raise Exception("could not acquire the lock")

            tbot.log.message(f"Acquired lock {self.lock_name}")
            yield None


class PooledMachineLock(machine.PreConnectInitializer):
    """
    A 'replacement' for `MachineLock` which acquires a lock from a pool.
    """

    lock_expiry: typing.Optional[int] = None
    selected_machine: typing.Optional[str]

    @property
    @abc.abstractmethod
    def available_machines(self) -> typing.List[str]:
        """
        Abstract property containing names of machines in the pool
        """
        raise tbot.error.AbstractMethodError()

    @contextlib.contextmanager
    def _init_pre_connect(self) -> typing.Iterator:
        with tbot.ctx.request(tbot.role.LabHost) as labhost:
            if not isinstance(labhost, LockManagerBase):
                raise Exception("selected lab-host is not a lock manager")
            self.selected_machine = None
            for name in self.available_machines:  # iterate through machines
                if labhost.request_machine_lock(name, expiry=self.lock_expiry):
                    self.selected_machine = name
                    break
            if self.selected_machine is None:
                raise Exception("Could not get free lock")

            tbot.log.message(f"Acquired lock for {self.selected_machine}")
            yield None


@contextlib.contextmanager
def flock_file_mutex(path: linux.Path, lock_fd: int) -> typing.Iterator[None]:
    """
    A context for holding a flock lock while running mutual exclusive code
    """
    host = path.host
    try:
        host.exec0("exec", linux.Raw(f"{lock_fd}>"), path)
        host.exec0("flock", str(lock_fd))
        yield None
    finally:
        host.exec0("flock", "-u", str(lock_fd))
        host.exec0("exec", linux.Raw(f"{lock_fd}>&-"))


class LockManager(LockManagerBase, machine.PostShellInitializer, linux.LinuxShell):
    """
    Machine locking implementation based on Python, bash and flock(1)
    """

    lock_checkpid: bool = True
    """
    Make tbot check whether the PID associated with a lockfile is still alive.

    If this check is enabled and the PID is found, the lock will be considered
    active, even if it would otherwise have been assumed expired.
    """
    lock_fd: int = 9  # Default file descriptor in shell for lock file

    _active_locks: typing.Set[str]  # list of active locks

    @property
    def lock_dir(self) -> linux.Path:
        """
        The directory where tbot locks are stored.

        Defaults to ``/tmp/tbot-locks``.  If this directory does not exist, it
        will be created and given ``0777`` access mode to allow all users to
        write lockfiles to it.
        """
        return self.fsroot / "tmp" / "tbot-locks"

    def _lock_try_acquire(self, name: str, expiry: typing.Optional[int]) -> bool:
        lockfile = self.lock_dir / name
        retval, result = self.exec("mktemp", "-p", self.lock_dir, "lock.XXX")
        if retval != 0:
            raise Exception("Could not create tempfile")
        tempfile = linux.Path(self, result.strip())
        if (expiry is None) or (expiry < 1):  # if lock does not expire
            time_str = "0"
        else:  # else store the Unix time timestamp of expiry
            time_str = str(int(self.exec0("date", "+%s")) + expiry)
        shell_pid = self.env("$") if self.lock_checkpid else "0"
        tempfile.write_text(f"{time_str} {shell_pid}\n")
        # Try linking lockfile, hard-linking is atomic
        lock_acquired = self.test("ln", tempfile, lockfile)
        self.exec0("rm", tempfile)
        return lock_acquired

    def _lock_handle_expiry(self, name: str) -> bool:
        lockfile = self.lock_dir / name
        locklock = self.lock_dir / "lock-lock"
        with flock_file_mutex(locklock, self.lock_fd):
            # Read the lock, perhaps it is stale...
            retval, result = self.exec("cat", lockfile)
            if retval != 0:
                return False
            retry = False
            results = result.split()
            # Check if the lock can expire, and whether it has expired.
            if (int(results[0]) != 0) and (
                int(results[0]) < int(self.exec0("date", "+%s"))
            ):
                # Check whether the lock PID is still in use by a bash instance
                retval, result = self.exec("ps", "-ocomm=", results[1])
                if (retval == 0) and (result.strip() == "bash"):
                    tbot.log.message(
                        f"Expired lock {lockfile} PID still appears valid!"
                    )
                else:
                    self.release_machine_lock(name)  # Delete stale Lock
                    tbot.log.message(f"Lock {lockfile} expired, deleted.")
                    retry = True  # The stale lock may be available next time round.
        return retry

    def request_machine_lock(
        self, name: str, *, expiry: typing.Optional[int] = None
    ) -> bool:
        if not self.lock_dir.is_dir():
            self.exec0("mkdir", self.lock_dir)
            self.exec0("chmod", "0777", self.lock_dir)
        if not self._lock_try_acquire(name, expiry):
            if not self._lock_handle_expiry(name):
                return False  # locked and not expired
            if not self._lock_try_acquire(name, expiry):  # expired, can retry
                return False  # no luck this time
        self._active_locks.add(name)
        return True

    def release_machine_lock(self, name: str) -> None:
        """
        Release lock for machine named ``name``.

        If not explicitly released, the
        :py:class:`~tbot_contrib.locking.LockManager` will automatically unlock
        all locks it is holding when the lab-host machine is deinitialized.
        """
        lockfile = self.lock_dir / name
        self._active_locks.discard(name)
        self.exec("rm", lockfile)

    @contextlib.contextmanager
    def _init_post_shell(self) -> typing.Iterator:
        self._active_locks = set()
        if not tbot.tc.shell.check_for_tool(self, "flock"):
            raise NotImplementedError()
        try:
            yield None
        finally:
            # Locks are released when the lab-host exits.
            for lock in list(self._active_locks):
                self.release_machine_lock(lock)
