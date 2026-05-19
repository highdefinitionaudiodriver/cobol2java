      ******************************************************************
      * Sample COBOL — Order Entry (CC0 / public domain)
      * 難易度 2 想定: PERFORM / IF / EVALUATE / 簡単な算術。
      ******************************************************************
       IDENTIFICATION DIVISION.
       PROGRAM-ID. ORDENTRY.

       DATA DIVISION.
       WORKING-STORAGE SECTION.
       01  WS-ORDER-INPUT.
           05  WS-CUSTOMER-ID    PIC 9(8).
           05  WS-PRODUCT-ID     PIC X(10).
           05  WS-QUANTITY       PIC 9(5).
           05  WS-UNIT-PRICE     PIC 9(7)V99 COMP-3.

       01  WS-ORDER-TOTAL        PIC 9(11)V99 COMP-3.
       01  WS-DISCOUNT-RATE      PIC V99      COMP-3 VALUE ZERO.
       01  WS-DISCOUNT-AMT       PIC 9(11)V99 COMP-3.
       01  WS-NET-AMT            PIC 9(11)V99 COMP-3.

       01  WS-PRODUCT-CATEGORY   PIC X.
           88  IS-FOOD                 VALUE 'F'.
           88  IS-CLOTH                VALUE 'C'.
           88  IS-ELECTRONICS          VALUE 'E'.

       01  WS-LOOP-COUNTER       PIC 9(3).
       01  WS-MAX-LINES          PIC 9(3) VALUE 50.

       PROCEDURE DIVISION.
       MAIN-PARA.
           PERFORM INIT-PARA.
           PERFORM PROCESS-LINE
               VARYING WS-LOOP-COUNTER FROM 1 BY 1
               UNTIL WS-LOOP-COUNTER > WS-MAX-LINES.
           PERFORM SUMMARY-PARA.
           STOP RUN.

       INIT-PARA.
           MOVE ZERO TO WS-ORDER-TOTAL.
           MOVE 'F' TO WS-PRODUCT-CATEGORY.

       PROCESS-LINE.
           COMPUTE WS-NET-AMT = WS-QUANTITY * WS-UNIT-PRICE.

           EVALUATE TRUE
               WHEN IS-FOOD
                   MOVE 0.05 TO WS-DISCOUNT-RATE
               WHEN IS-CLOTH
                   MOVE 0.10 TO WS-DISCOUNT-RATE
               WHEN IS-ELECTRONICS
                   IF WS-NET-AMT > 100000
                       MOVE 0.15 TO WS-DISCOUNT-RATE
                   ELSE
                       MOVE 0.08 TO WS-DISCOUNT-RATE
                   END-IF
               WHEN OTHER
                   MOVE ZERO TO WS-DISCOUNT-RATE
           END-EVALUATE.

           COMPUTE WS-DISCOUNT-AMT = WS-NET-AMT * WS-DISCOUNT-RATE.
           COMPUTE WS-NET-AMT = WS-NET-AMT - WS-DISCOUNT-AMT.
           ADD WS-NET-AMT TO WS-ORDER-TOTAL.

       SUMMARY-PARA.
           DISPLAY 'ORDER TOTAL: ' WS-ORDER-TOTAL.

       END PROGRAM ORDENTRY.
