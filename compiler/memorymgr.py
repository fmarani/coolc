fp_offset = 0


def enter_frame():
    global fp_offset
    fp_offset = 0


def codestack_push(bytes):
    global fp_offset
    fp_offset -= bytes
    return "addi $sp, $sp, -" + str(bytes)
