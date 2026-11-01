"""Spawn one isolated process per job; cancellation kills that process tree."""
import multiprocessing as mp
import os
import signal
import subprocess
import queue
import time
import tempfile
from pathlib import Path


def remove_partial(target):
    """Windows may release child-process file handles shortly after termination."""
    for attempt in range(21):
        try:
            Path(target).unlink(missing_ok=True)
            return
        except PermissionError:
            if attempt == 20:raise
            time.sleep(.05)


def child_job(job,target,messages,temporary_root):
    tempfile.tempdir=temporary_root
    if os.name!='nt':
        os.setsid()
    import conversion_progress
    conversion_progress.CALLBACK=lambda fraction,phase,eta:messages.put(('progress',fraction,phase,eta))
    try:
        from engine import convert
        from operations import execute
        operation=job.get('operation','convert')
        if operation=='convert':
            result=convert(job['sources'][0],str(Path(target).parent),job['format'],job.get('options',{}),target=target)
        else:
            execute(operation,job['sources'],target,job['format'],job.get('options',{}));result=str(target)
        messages.put(('done',True,result))
    except Exception as error:
        remove_partial(target)
        messages.put(('done',False,str(error)))


def kill_tree(process):
    if process.pid is None:return
    if os.name=='nt':
        subprocess.run(['taskkill','/PID',str(process.pid),'/T','/F'],capture_output=True,
                       creationflags=getattr(subprocess,'CREATE_NO_WINDOW',0))
    else:
        try:os.killpg(process.pid,signal.SIGKILL)
        except ProcessLookupError:
            if process.is_alive():process.kill()
        except PermissionError:process.kill()
    process.join(timeout=3)
    if process.is_alive():process.kill();process.join(timeout=3)


def run_job(job,target,cancelled,progress):
    if cancelled():
        remove_partial(target)
        return None,'Annullato'
    directory=tempfile.TemporaryDirectory(prefix='convertitore-job-')
    context=mp.get_context('spawn');messages=context.Queue();process=context.Process(target=child_job,args=(job,str(target),messages,directory.name))
    result=None
    try:
        process.start()
        while True:
            if cancelled():
                kill_tree(process);remove_partial(target)
                return None,'Annullato'
            try:
                message=messages.get(timeout=.05)
                if message[0]=='progress':progress(*message[1:])
                elif message[0]=='done':result=message;break
            except queue.Empty:
                if not process.is_alive():
                    try:
                        message=messages.get(timeout=.2)
                        if message[0]=='done':result=message;break
                    except queue.Empty:break
        process.join(timeout=3)
        if process.is_alive():kill_tree(process)
        if result:
            return result[1],result[2]
        remove_partial(target)
        return False,'Il processo di conversione si è chiuso senza produrre un risultato.'
    except Exception:
        if process.is_alive():kill_tree(process)
        remove_partial(target)
        raise
    finally:
        if process.is_alive():kill_tree(process)
        messages.close();messages.join_thread();directory.cleanup()
