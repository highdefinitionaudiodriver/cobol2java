      ******************************************************************
      * Sample COBOL — Billing Procedure (CC0 / public domain)
      * 難易度 4 想定: EXEC SQL (DB2 想定)、GO TO 多用、複雑な制御フロー。
      ******************************************************************
       IDENTIFICATION DIVISION.
       PROGRAM-ID. BILLPROC.

       DATA DIVISION.
       WORKING-STORAGE SECTION.
           COPY CUSTOMER.
           COPY COMMON.

       01  WS-SQLCA.
           EXEC SQL INCLUDE SQLCA END-EXEC.

       01  WS-INVOICE.
           05  WS-INV-NO              PIC 9(10).
           05  WS-INV-DATE            PIC 9(8).
           05  WS-INV-CUST-ID         PIC 9(8).
           05  WS-INV-AMOUNT          PIC S9(11)V99 COMP-3.
           05  WS-INV-TAX             PIC S9(11)V99 COMP-3.
           05  WS-INV-STATUS          PIC X.

       01  WS-TAX-RATE                PIC V9999 COMP-3 VALUE 0.1000.
       01  WS-TOTAL-INVOICES          PIC 9(7) VALUE ZERO.
       01  WS-ERROR-FLAG              PIC X VALUE 'N'.

       PROCEDURE DIVISION.
       MAIN-PARA.
           PERFORM INIT-PARA.

           EXEC SQL
               DECLARE INV-CURSOR CURSOR FOR
                   SELECT INV_NO, INV_DATE, CUST_ID, AMOUNT
                     FROM INVOICES
                    WHERE STATUS = 'PENDING'
                 ORDER BY INV_NO
           END-EXEC.

           EXEC SQL OPEN INV-CURSOR END-EXEC.
           IF SQLCODE NOT = 0
               GO TO ERROR-EXIT.

       FETCH-LOOP.
           EXEC SQL FETCH INV-CURSOR INTO
                   :WS-INV-NO, :WS-INV-DATE, :WS-INV-CUST-ID,
                   :WS-INV-AMOUNT
           END-EXEC.

           IF SQLCODE = 100
               GO TO CLOSE-CURSOR.
           IF SQLCODE NOT = 0
               GO TO ERROR-EXIT.

           PERFORM PROCESS-INVOICE.
           ADD 1 TO WS-TOTAL-INVOICES.
           GO TO FETCH-LOOP.

       PROCESS-INVOICE.
           COMPUTE WS-INV-TAX = WS-INV-AMOUNT * WS-TAX-RATE.

           EXEC SQL
               UPDATE INVOICES
                  SET TAX = :WS-INV-TAX,
                      STATUS = 'INVOICED'
                WHERE INV_NO = :WS-INV-NO
           END-EXEC.

           IF SQLCODE NOT = 0
               MOVE 'Y' TO WS-ERROR-FLAG
               GO TO ERROR-EXIT.

       CLOSE-CURSOR.
           EXEC SQL CLOSE INV-CURSOR END-EXEC.
           EXEC SQL COMMIT END-EXEC.
           GO TO EXIT-PARA.

       ERROR-EXIT.
           EXEC SQL ROLLBACK END-EXEC.
           DISPLAY 'ERROR DURING BILLING, SQLCODE = ' SQLCODE.

       EXIT-PARA.
           DISPLAY 'PROCESSED INVOICES: ' WS-TOTAL-INVOICES.
           STOP RUN.

       INIT-PARA.
           ACCEPT WS-CURRENT-DATE FROM DATE YYYYMMDD.

       END PROGRAM BILLPROC.
