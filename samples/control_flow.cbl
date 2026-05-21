       IDENTIFICATION DIVISION.
       PROGRAM-ID. CTRLFLOW.
       DATA DIVISION.
       WORKING-STORAGE SECTION.
       01 WS-FLAGS.
          05 WS-EOF-FLAG PIC X VALUE "N".
             88 WS-EOF VALUE "Y".
             88 WS-NOT-EOF VALUE "N".
          05 WS-ERROR-FLAG PIC X VALUE "N".
             88 WS-HAS-ERROR VALUE "Y".
             88 WS-NO-ERROR VALUE "N".
          05 WS-GRADE PIC X VALUE " ".
       01 WS-COUNTERS.
          05 WS-OUTER-CTR PIC 9(3) VALUE 0.
          05 WS-INNER-CTR PIC 9(3) VALUE 0.
       PROCEDURE DIVISION.
       000-MAIN-CONTROL.
           PERFORM 100-INITIALIZE.
           PERFORM 200-PROCESS UNTIL WS-EOF.
           STOP RUN.
       100-INITIALIZE.
           MOVE 0 TO WS-OUTER-CTR.
       200-PROCESS.
           ADD 1 TO WS-OUTER-CTR.
           PERFORM 300-INNER-LOOP VARYING WS-INNER-CTR FROM 1 BY 1 UNTIL WS-INNER-CTR > 10.
       300-INNER-LOOP.
           PERFORM 400-CALCULATE.
           PERFORM 500-VALIDATE.
           IF WS-OUTER-CTR > 8
              GO TO 300-INNER-LOOP-EXIT
           END-IF.
       300-INNER-LOOP-EXIT.
           EXIT.
       400-CALCULATE.
           IF WS-OUTER-CTR > 5
              ADD 1 TO WS-OUTER-CTR
           ELSE
              ADD 2 TO WS-OUTER-CTR
           END-IF.
       500-VALIDATE.
           EVALUATE WS-OUTER-CTR
               WHEN 1
                   MOVE "A" TO WS-GRADE
               WHEN 2
                   MOVE "B" TO WS-GRADE
               WHEN 3
                   MOVE "C" TO WS-GRADE
               WHEN OTHER
                   MOVE "F" TO WS-GRADE
           END-EVALUATE.
           IF WS-GRADE = "A"
              IF WS-OUTER-CTR > 3
                 SET WS-EOF TO TRUE
              END-IF
           ELSE
              IF WS-OUTER-CTR < 2
                 SET WS-HAS-ERROR TO TRUE
              END-IF
           END-IF.
