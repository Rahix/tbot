import random
import socket
import tbot


@tbot.testcase
def selftest_buildhost(tb: tbot.TBot) -> None:
    random_string = str(random.randint(1000, 9999))
    if len(tb.config["build", []]) > 1:
        with tb.machine(tbot.machine.MachineBuild()) as tb:
            tb.shell.exec0("uname -a")
            tb.shell.exec0("FOOBAR123='314'")
            buildfile = tb.shell.workdir / "test-file.txt"
            toolchain = tb.call("toolchain_get")

            @tb.call_then("toolchain_env", toolchain=toolchain)
            def in_env(tb: tbot.TBot) -> None:
                tb.shell.exec0("echo $CC")
                ret = tb.shell.exec0("echo $FOOBAR123").strip()
                assert ret == "314", "Environment is not persistent"

            tb.shell.exec0(f"mkdir -p {buildfile.parent}")
            tb.shell.exec0(f"echo '{random_string}'>{buildfile}")

        labhost_file = tb.call("retrieve_build_artifact", buildfile=buildfile)
        content = tb.shell.exec0(f"cat {labhost_file}").strip()
        assert content == random_string, "File from buildhost has wrong content"

    else:
        tbot.log.message("Skipping buildhost test, because no buildhost was found")


@tbot.testcase
def selftest_buildhost_bad_ssh(tb: tbot.TBot) -> None:
    raised = False
    try:
        with tb.machine(
            tbot.machine.MachineBuild(
                name="custom_fail", ssh_command="ssh nobody@nonexistant-host"
            )
        ) as tb:
            raise Exception(
                "Somehow TBot thinks that it just succeeded connecting to \
a host that does not exist"
            )
    except socket.error:
        raised = True
    assert raised, "Connection to buildhost failed silently"
