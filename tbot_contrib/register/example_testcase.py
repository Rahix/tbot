import tbot
from register import CPU


@tbot.testcase
def testcase_prueba() -> None:

    with tbot.acquire_lab() as lb:
        with tbot.acquire_board(lb) as b:
            with tbot.acquire_uboot(b) as ub:
                cpu2 = CPU(ub, processor_name="iMX6SDL")
                cpu2.read_register("VDI_PS_4")
                cpu2.write_register("VDI_PS_4", 0x1)
                cpu2.read_register("VDI_PS_4")
                # cpu2.read_all_registers_from_group("IPU")
                with tbot.acquire_linux(ub) as lx:
                    cpu2.set_host(lx)
                    # cpu2.read_register("GPUSR1")
                    # cpu2.read_all_registers_from_group("IPU")
                    cpu2.read_register("VDI_PS_4")
                    cpu2.write_register("VDI_PS_4", 0x12)
                    cpu2.read_register("VDI_PS_4")
