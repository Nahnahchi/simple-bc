from shutil import copytree, copy2
from threading import Thread
from os import _exit
from datetime import datetime
from collections import defaultdict
from time import sleep
from os.path import exists, join, basename, normpath
from os import system, mkdir, name
from pickle import dump, load, UnpicklingError


ID = 0
LOG = []
PROC_STATUS = defaultdict(list)
DESTINATION = "backups"
CONFIG = "config.dat"


def backup(src_type, src_path, dst_path):
    if not exists(dst_path):
        mkdir(dst_path)
        LOG.append("Created directory '%s'" % basename(normpath(dst_path)))
    now = datetime.now()
    date_time = now.strftime("%m-%d-%Y_%H-%M-%S")
    dst_path = join(dst_path, date_time)
    if src_type == "d":
        copytree(src_path, dst_path, copy_function=copy2)
    elif src_type == "f":
        if not exists(dst_path):
            mkdir(dst_path)
        copy2(src_path, dst_path)
    else:
        raise TypeError("wrong file type")
    LOG.append("Backed up %s '%s'" % ("FILE" if src_type == "f" else "FOLDER", basename(normpath(src_path))))


def cls():
    system('cls' if name == 'nt' else 'clear')


def run(proc_id, src_type, src_path, dst_path, slp_time):
    LOG.append("Started new backup process on %s '%s', ID: %d" % ("file" if src_type == "f" else "directory",
                                                                  basename(normpath(src_path)), proc_id))
    while PROC_STATUS[proc_id][0]:
        try:
            backup(src_type, src_path, dst_path)
            sleep(slp_time)
        except (PermissionError, NotADirectoryError, FileNotFoundError, OSError) as err:
            LOG.append(err)
            break
        except ValueError as err:
            LOG.append("[Error] " + str(err))
            break
    del PROC_STATUS[proc_id]
    save_proc()
    LOG.append("Stopped backup process [%d]" % proc_id)


def format_path(path):
    if path[0] == "\"" and path[-1] == "\"":
        return path[1:-1]
    if path[0] == "'" and path[-1] == "'":
        return path[1:-1]
    return path


def save_proc():
    with open(CONFIG, "wb") as conf:
        dump(PROC_STATUS, conf)


def run_interface():

    global ID, PROC_STATUS, LOG

    print("--------------------------")
    print("Select an option:")
    print("0. Exit program")
    print("1. Backup a file")
    print("2. Backup a directory")
    print("3. Read log")
    print("4. Review backup processes")

    inp = input("~ ")

    cls()

    if inp == "0":

        _exit(0)

    elif inp in ("1", "2"):

        src_path = format_path(input("Path to the %s: " % ("file" if inp == "1" else "directory")))
        src_name = basename(normpath(src_path))
        dst_path = join(DESTINATION, src_name + "-" + str(ID))
        slp_time = input("Time interval between backups (s): ")
        src_type = "f" if inp == "1" else "d"
        try:
            slp_time = int(slp_time)
            PROC_STATUS[ID] = [True, src_name, slp_time, src_type, src_path, dst_path]
            save_proc()
            Thread(target=run, args=(ID, src_type, src_path, dst_path, slp_time)).start()
            ID += 1
        except ValueError as err:
            print(err)

    elif inp == "3":

        for entry in LOG:
            print(entry)

    elif inp == "4":

        for pid in PROC_STATUS.keys():
            if PROC_STATUS[pid][0]:
                print("[%d] '%s' every %ds" % (pid, PROC_STATUS[pid][1], PROC_STATUS[pid][2]))

        print("--------------------------")
        print("0. Return")
        print("1. Stop process")
        print("2. Stop all processes")

        try:
            opt = input("~ ")
            if opt == "0":
                pass
            elif opt == "1":
                pid = int(input("Enter process ID: "))
                if pid not in PROC_STATUS.keys():
                    raise IndexError("list index out of range")
                else:
                    PROC_STATUS[pid][0] = False
                    save_proc()
            elif opt == "2":
                print("Are you sure you want to stop all backup processes? (Y/N)")
                ans = input("~ ").upper()
                if ans == "Y":
                    for pid in PROC_STATUS:
                        PROC_STATUS[pid][0] = False
                    save_proc()
        except (ValueError, IndexError) as err:
            print(err)


if __name__ == "__main__":

    if exists(CONFIG):
        with open(CONFIG, "rb") as config:
            try:
                PROC_STATUS = load(config)
                if bool(PROC_STATUS):
                    processes = defaultdict(Thread)
                    for process_id in PROC_STATUS.keys():
                        print(process_id)
                        sleep_time = PROC_STATUS[process_id][2]
                        source_type = PROC_STATUS[process_id][3]
                        source_path = PROC_STATUS[process_id][4]
                        dest_path = PROC_STATUS[process_id][5]
                        processes[process_id] = Thread(
                            target=run,
                            args=(process_id, source_type, source_path, dest_path, sleep_time)
                        )
                    for proc in processes.values():
                        proc.start()
                    ID = list(PROC_STATUS.keys())[-1] + 1
            except (EOFError, UnpicklingError):
                PROC_STATUS = defaultdict(list)
                LOG.append("Couldn't load process list")

    while True:
        if not exists(DESTINATION):
            mkdir(DESTINATION)
            LOG.append("Created 'backup' directory")
        try:
            run_interface()
        except TypeError as e:
            print(e)
