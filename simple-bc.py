from shutil import copytree, copy2
from threading import Thread
from sys import exit
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

def backup(type, src, dst):
    if not exists(dst):
        mkdir(dst)
        LOG.append("Created directory '%s'" % basename(normpath(dst)))
    now = datetime.now()
    date_time = now.strftime("%m-%d-%Y_%H-%M-%S")
    dst = join(dst, date_time)
    if type == "d":
        copytree(src, dst, copy_function=copy2)
    elif type == "f":
        if not exists(dst):
            mkdir(dst)
        copy2(src, dst)
    else:
        raise TypeError("wrong file type")
    LOG.append("Backed up %s '%s'" % ("FILE" if type == "f" else "FOLDER", basename(normpath(src))))

def cls():
    system('cls' if name == 'nt' else 'clear')

def run(id, type, src, dst, slp):
    LOG.append("Started new backup process on %s '%s', ID: %d" % ("file" if type == "f" else "directory", basename(normpath(src)), id))
    while PROC_STATUS[id][0] == True:
        try:
            backup(type, src, dst)
            sleep(slp)
        except PermissionError as e:
            LOG.append(e)
            break
        except NotADirectoryError as e:
            LOG.append(e)
            break
        except ValueError as e:
            LOG.append("[Error] " + e)
            break
        except FileNotFoundError as e:
            LOG.append(e)
            break
        except OSError as e:
            LOG.append(e)
            break
    del PROC_STATUS[id]
    save_proc()
    LOG.append("Stopped backup proccess [%d]" % id)

def format_path(path):
    if path[0] == "\"" and path[len(path) - 1] == "\"":
        return path[1:len(path) - 1]
    if path[0] == "'" and path[len(path) - 1] == "'":
        return path[1:len(path) - 1]
    return path

def save_proc():
    with open(CONFIG, "wb") as conf:
        dump(PROC_STATUS, conf)

def interface():
    global ID, PROC_STATUS, LOG
    print("--------------------------")
    print("Select an option:")
    print("0. Exit program")
    print("1. Backup file")
    print("2. Backup directory")
    print("3. Read log")
    print("4. Review backup processes")
    inp = input("~ ")
    cls()
    if inp == "0":
        exit(0)
    elif inp == "1" or inp == "2":
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
        except ValueError as e:
            print(e)
    elif inp == "3":
        for entry in LOG:
            print(entry)
    elif inp == "4":
        for id in PROC_STATUS.keys():
            if PROC_STATUS[id][0] == True:
                print("[%d] '%s' every %ds" % (id, PROC_STATUS[id][1], PROC_STATUS[id][2]))
        print("--------------------------")
        print("0. Return")
        print("1. Stop process")
        print("2. Stop all processes")
        try:
            opt = input("~ ")
            if opt == "0":
                pass
            elif opt == "1":
                id = int(input("Enter process ID: "))
                if not id in PROC_STATUS.keys():
                    raise IndexError("list index out of range")
                else:
                    PROC_STATUS[id][0] = False
                    save_proc()
            elif opt == "2":
                print("Are you sure you want to stop all backup processes? (Y/N)")
                ans = input("~ ").upper()
                if ans == "Y":
                    for id in PROC_STATUS:
                        PROC_STATUS[id][0] = False
                    save_proc()
        except ValueError as e:
            print(e)
        except IndexError as e:
            print(e)

if __name__ == "__main__":
    if exists(CONFIG):
        with open(CONFIG, "rb") as conf:
            try:
                PROC_STATUS = load(conf)
                if bool(PROC_STATUS) == True:
                    processes = defaultdict(list)
                    for id in PROC_STATUS:
                        slp_time = PROC_STATUS[id][2]
                        src_type = PROC_STATUS[id][3]
                        src_path = PROC_STATUS[id][4]
                        dst_path = PROC_STATUS[id][5]
                        processes[id] = Thread(target=run, args=(id, src_type, src_path, dst_path, slp_time))
                    for proc in processes.values():
                        proc.start()
                    ID = list(PROC_STATUS.keys())[-1] + 1
            except EOFError:
                PROC_STATUS = defaultdict(list)
                LOG.append("Couldn't load process list")
            except UnpicklingError:
                PROC_STATUS = defaultdict(list)
                LOG.append("Couldn't load process list")
    while True:
        if not exists(DESTINATION):
            mkdir(DESTINATION)
            LOG.append("Created 'backup' directory")
        try:
            interface()
        except TypeError as e:
            print(e)
