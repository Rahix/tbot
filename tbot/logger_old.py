class LogLevel:
    ERROR = 10
    WARNING = 9
    INFO = 9
    STDOUT = 7
    DEBUG = 6
    TRACE = 5


class Logger:
    def __init__(self, stdout_level, logfile_level, logfile):
        self.stdout_level = stdout_level
        self.logfile_level = logfile_level
        self.logfile = open(logfile, mode="w")

    def log(self, level, msg):
        if level >= self.stdout_level:
            print(msg)
        if level >= self.logfile_level:
            self.logfile.write(msg)
            self.logfile.write("\n")
            self.logfile.flush()

    def log_error(self, msg):
        self.log(LogLevel.ERROR, msg)

    def log_warning(self, msg):
        self.log(LogLevel.WARNING, msg)

    def log_info(self, msg):
        self.log(LogLevel.INFO, msg)

    def log_stdout(self, msg):
        self.log(LogLevel.STDOUT, msg)

    def log_debug(self, msg):
        self.log(LogLevel.DEBUG, msg)

    def log_trace(self, msg):
        self.log(LogLevel.TRACE, msg)
