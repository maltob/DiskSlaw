from subprocess import call,Popen

#Wrapper function around setterm to disable the screen blanking out
def disable_terminal_blanking():
    call(["setterm","-blank","0","-powerdown","0",])

#Wrapper around pm-suspend to put computer to sleep
def suspend_computer():
    proc = Popen(['pm-suspend'])
    proc.communicate()