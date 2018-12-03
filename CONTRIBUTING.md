Contributing to tbot
====================

Hello there!  Thank you for taking your time to help *tbot* become a better
piece of software!  To make this go as smoothly as possible, please follow the
guidelines below:

## Commit Style
### `pre-commit`
When sending a pull-request or patch, please make sure to use the supplied
[pre-commit](https://pre-commit.com/) config.  To do so, install the tool and
run `pre-commit install` inside the repository.  Now, if you `git commit`,
*pre-commit* will run a bunch of tests to ensure your changes don't break
anything else!

If you commits touch the `tbot.tc` module, please also run `tbot selftest_tc`
to make sure nothing broke in there.

### Commit Messages
Your commit messages should look like this:
`<relevant part>: Message in imperative style (present tense)`

If your changes apply to tbot as a whole, you can leave out the `<module>:`.
Examples:

```text
board.uboot: Fix bootlog missing if not autobooting
doc: Add flags documentation
loader: Show traceback of errrors
Fix a few spelling mistakes
```

### Changelog
Please add your changes to `CHANGELOG.md` in your commits as well.  This way,
the changelog grows alongside the project and doesn't need to be written
retrospectively.  Add your changes under `## [Unreleased]`, following the
conventions from [keep-a-changelog](https://keepachangelog.com/en/1.0.0/).

If your changes require non-trivial downstream fixes, please add a short
migration-guide as well.


## Coding Style
### Type-Annotations
Your code should always use type annotations and pass a check using mypy.  You
can most easily check if that is the case by using the supplied *pre-commit*
config.

### Formatting
Formatting convention is [black](https://github.com/ambv/black), this is also
enforced by the *pre-commit* config.  Just write code however you want and let
*black* format it for you ;)

### Imports
Please don't import things into your namespace that you don't explicitly want
to have available for downstream users.  Prefer importing the module to keep
your namespace clean and to give readers the ability to easily see where some
object was pulled in from.

**Good**:

```python
from tbot.machine import channel

# Later on
def foo() -> channel.Channel:
    ...
```

**Bad**:

```python
from tbot.machine.channel import Channel

# Now Channel is polluting our namespace :(
def foo() -> Channel:
    ...
```

There might be some exceptions where the latter is definitely perferable, but
in most cases it isn't.

## Design
When thinking about how to design your additions, please take some time to check
if your ideas follow the [Zen of Python](https://www.python.org/dev/peps/pep-0020/).
*tbot* should be kept as elegant and small as possible, we don't want huge new
features in *tbot* that could also fit into their own module.

**Prefer composition over configuration.**  Or as the kernel calls it: *Mechanism,
not policy.*  tbot should be flexible and generic over the users needs.  Don't
force anything on the user that they might want differently!
