# tbot, Embedded Automation Tool
# Copyright (C) 2019  Harald Seiler
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <https://www.gnu.org/licenses/>.

from .. import linux


class Lab(linux.LinuxShell):
    """
    Mixin for marking a machine as a lab-host.
    """

    def build(self) -> linux.Builder:
        """
        Return the default build-host for this lab.

        If your lab does not contain a build-capable machine, just leave this
        method as is.  tbot will raise an exception if a testcase attempts
        accessing the build-host anyway.
        """
        raise KeyError("No build machine available!")
