      ******************************************************************
      * Sample COPYBOOK — Common Definitions (CC0 / public domain)
      ******************************************************************
       01  WS-DATE-FIELDS.
           05  WS-CURRENT-DATE        PIC 9(8).
           05  WS-CURRENT-TIME        PIC 9(6).
           05  WS-FISCAL-YEAR         PIC 9(4).
           05  WS-FISCAL-MONTH        PIC 99.
           05  WS-FISCAL-PERIOD       PIC 9(6).

       01  WS-ERROR-CODES.
           05  WS-ERR-NONE            PIC 9(4) VALUE 0000.
           05  WS-ERR-NOT-FOUND       PIC 9(4) VALUE 1001.
           05  WS-ERR-DUPLICATE       PIC 9(4) VALUE 1002.
           05  WS-ERR-INVALID-INPUT   PIC 9(4) VALUE 2001.
           05  WS-ERR-INSUFFICIENT    PIC 9(4) VALUE 3001.
           05  WS-ERR-SQL-FAILURE     PIC 9(4) VALUE 9001.
           05  WS-ERR-FILE-IO         PIC 9(4) VALUE 9002.
