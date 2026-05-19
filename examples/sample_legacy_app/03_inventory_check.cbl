      ******************************************************************
      * Sample COBOL — Inventory Check (CC0 / public domain)
      * 難易度 3 想定: COPY による共通レコード、INDEXED ファイル I/O、
      *                 サブプログラム呼出。
      ******************************************************************
       IDENTIFICATION DIVISION.
       PROGRAM-ID. INVCHK.

       ENVIRONMENT DIVISION.
       INPUT-OUTPUT SECTION.
       FILE-CONTROL.
           SELECT INV-FILE ASSIGN TO 'INVMAST.VSAM'
               ORGANIZATION IS INDEXED
               ACCESS MODE IS RANDOM
               RECORD KEY IS INV-PRODUCT-ID.

       DATA DIVISION.
       FILE SECTION.
       FD  INV-FILE.
       01  INV-RECORD.
           05  INV-PRODUCT-ID         PIC X(10).
           05  INV-PRODUCT-NAME       PIC X(60).
           05  INV-CATEGORY           PIC X(2).
           05  INV-ON-HAND            PIC 9(7) COMP-3.
           05  INV-RESERVED           PIC 9(7) COMP-3.
           05  INV-AVAILABLE REDEFINES INV-RESERVED PIC 9(7) COMP-3.
           05  INV-REORDER-POINT      PIC 9(5) COMP-3.
           05  INV-LOCATION-CODE      PIC X(6).

       WORKING-STORAGE SECTION.
           COPY CUSTOMER.
           COPY COMMON.

       01  WS-REQUEST.
           05  WS-REQ-PRODUCT-ID      PIC X(10).
           05  WS-REQ-QUANTITY        PIC 9(7).

       01  WS-RESPONSE.
           05  WS-RESP-CODE           PIC 9(4).
           05  WS-RESP-AVAILABLE      PIC 9(7).
           05  WS-RESP-MESSAGE        PIC X(80).

       PROCEDURE DIVISION.
       MAIN-PARA.
           OPEN I-O INV-FILE.
           PERFORM CHECK-INVENTORY.
           PERFORM LOG-AUDIT.
           CLOSE INV-FILE.
           STOP RUN.

       CHECK-INVENTORY.
           MOVE WS-REQ-PRODUCT-ID TO INV-PRODUCT-ID.
           READ INV-FILE
               INVALID KEY
                   MOVE WS-ERR-NOT-FOUND TO WS-RESP-CODE
                   MOVE 'PRODUCT NOT FOUND' TO WS-RESP-MESSAGE
               NOT INVALID KEY
                   PERFORM EVALUATE-AVAILABILITY.

       EVALUATE-AVAILABILITY.
           COMPUTE WS-RESP-AVAILABLE = INV-ON-HAND - INV-RESERVED.
           IF WS-RESP-AVAILABLE >= WS-REQ-QUANTITY
               MOVE WS-ERR-NONE TO WS-RESP-CODE
               MOVE 'OK' TO WS-RESP-MESSAGE
               ADD WS-REQ-QUANTITY TO INV-RESERVED
               REWRITE INV-RECORD
           ELSE
               MOVE WS-ERR-INSUFFICIENT TO WS-RESP-CODE
               MOVE 'INSUFFICIENT STOCK' TO WS-RESP-MESSAGE
           END-IF.

       LOG-AUDIT.
           CALL 'AUDITLOG' USING WS-REQUEST WS-RESPONSE.

       END PROGRAM INVCHK.
