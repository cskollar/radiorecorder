#########################
#LHFH radio recoder v1.0#
#########################

#settings
codec = "mp3"			  #"ogg" or "mp3"
quality = "64"			  #codec quality (-1 to 10 for ogg, "-9.2" for mp3 lowq vbr, 64 for standard 64kbps)
polling = 0.1			  #LPT polling interval (in sec, (0.1 = 100 msec)
debounce = 5			  #LPT polling interval (in sec) when recording in progress (also minimum length of a recorded tx)
inputdevice_tx = "hw:0"		  #input device for recording transmissions (see "arecord -L")
inputdevice_daily = "hw:1"	  #input device for recording daily audiofile (see "arecord -L")
logfile = "/var/log/recorder.log"  #logfile

#init modules
from datetime import datetime
import time
import os
import subprocess
import threading
import parallel
import logging

#tx recorder thread
def recorder_tx(name, stop):
    logging.info("Recorder-TX: started")
    #create directories if not exist
    now = datetime.now()
    txpath = now.strftime("/home/recorder-tx/%Y/%m/%d")
    os.makedirs(txpath, exist_ok=True)
    while True:
      txfile = now.strftime("/home/recorder-tx/%Y/%m/%d/%Y-%m-%d_%H-%M-%S." + codec)
      my_env = os.environ.copy()
      my_env["AUDIODEV"] = inputdevice_tx
      subprocess.run(["/usr/bin/sox", "-d", "-c", "1", "-C", quality, "-t", codec, txfile], env=my_env, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
      if stop():
        logging.info("Recoder-TX: stopped")
        break

#daily recorder thread
def recorder_daily(name, stop):
    logging.info("Recorder-DAILY: started")
    #create directories if not exist
    now = datetime.now()
    txpath = now.strftime("/home/recorder-daily/%Y/%m/%d")
    os.makedirs(txpath, exist_ok=True)
    while True:
      txfile = now.strftime("/home/recorder-daily/%Y/%m/%d/%Y-%m-%d_%H-%M-%S." + codec)
      my_env = os.environ.copy()
      my_env["AUDIODEV"] = inputdevice_daily
      subprocess.run(["/usr/bin/rec", "-c", "1", "-C", quality, "-t", codec, txfile], env=my_env, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
      if stop():
        logging.info("Recoder-DAILY: stopped")
        break

#main loop
def main():
    #init
    poll = polling
    stop_threads = False
    x = threading.Thread(target=recorder_tx, args=("recorder_tx", lambda: stop_threads))
    d = threading.Thread(target=recorder_daily, args=("recorder_daily", lambda: stop_threads))
    #START POLLING
    while True:
      #logging.info("Main: polling")
      #CONTROL TX RECORDER THREAD
      if p.getInSelected() == 1 and not x.is_alive():
        poll = debounce
        logging.info("Main: squelch signal detected, starting recorder-tx...")
        try:
          x.start()
        except RuntimeError:
          stop_threads = False
          x = threading.Thread(target=recorder_tx, args=("recorder_tx", lambda: stop_threads))
          x.start()
      elif p.getInSelected() == 0 and x.isAlive():
        logging.info("Main: squelch signal ended, stopping recoder-tx...")
        poll = polling
        subprocess.run(["killall", "-TERM", "sox"])
        stop_threads = True
        x.join(timeout=3)
      #CONTROL DAILY RECORDER THREAD
      now = datetime.now()
      dailypath = now.strftime("/home/recorder-daily/%Y/%m/%d")
      if not d.is_alive():
        logging.info("Main: daily recoder is not alive, starting...")
        try:
          d.start()
        except RuntimeError:
          stop_threads = False
          d = threading.Thread(target=recorder_daily, args=("recorder_daily", lambda: stop_threads))
          d.start()
      elif not os.path.exists(dailypath) and d.isAlive():
        logging.info("Main: rotating daily file, stopping recorder-tx...")
        subprocess.run(["killall", "-TERM", "rec"])
        stop_threads = True
        d.join(timeout=3)
      time.sleep(poll)

#init main
if __name__ == '__main__':
    #init parport
    p = parallel.Parallel()  # open /dev/parport0
    #init logger
    format = "%(asctime)s: %(message)s"
    logging.basicConfig(filename=logfile,format=format, level=logging.INFO,
			datefmt="%H:%M:%S")
    logging.info("----------------------------")
    logging.info("##### RECORDER STARTED #####")
    logging.info("----------------------------")
    main()
