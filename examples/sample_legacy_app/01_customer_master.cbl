      ******************************************************************
      * Sample COBOL — Customer Master (CC0 / public domain)
      * 難易度 1 想定: 単純な DATA + PROCEDURE のみ。
      * 移行先候補: Plain Java POJO + DAO
      ******************************************************************
       IDENTIFICATION DIVISION.
       PROGRAM-ID. CUSTMNT.
       AUTHOR. SAMPLE.

       ENVIRONMENT DIVISION.
       INPUT-OUTPUT SECTION.
       FILE-CONTROL.
           SELECT CUST-FILE ASSIGN TO 'CUSTMAST.DAT'
               ORGANIZATION IS SEQUENTIAL
               ACCESS MODE IS SEQUENTIAL.

       DATA DIVISION.
       FILE SECTION.
       FD  CUST-FILE.
       01  CUST-RECORD.
           05  CUST-ID            PIC 9(8).
           05  CUST-NAME          PIC X(40).
           05  CUST-ADDRESS       PIC X(80).
           05  CUST-PHONE         PIC X(15).
           05  CUST-CREDIT-LIMIT  PIC 9(9)V99 COMP-3.

       WORKING-STORAGE SECTION.
       01  WS-EOF-FLAG            PIC X VALUE 'N'.
           88  WS-EOF                   VALUE 'Y'.
           88  WS-NOT-EOF               VALUE 'N'.
       01  WS-RECORD-COUNT        PIC 9(7) VALUE ZERO.

       PROCEDURE DIVISION.
       MAIN-PARA.
           OPEN INPUT CUST-FILE.
           PERFORM READ-PARA UNTIL WS-EOF.
           DISPLAY 'TOTAL RECORDS PROCESSED: ' WS-RECORD-COUNT.
           CLOSE CUST-FILE.
           STOP RUN.

       READ-PARA.
           READ CUST-FILE
               AT END SET WS-EOF TO TRUE
               NOT AT END
                   ADD 1 TO WS-RECORD-COUNT
                   DISPLAY CUST-ID ' ' CUST-NAME.

       END PROGRAM CUSTMNT.
