      ******************************************************************
      * Sample COBOL — Period Close (CC0 / public domain)
      * 難易度 5 想定: CICS + DLI 混在、ALTER 文、複雑な PERFORM THRU、
      *                 ネスト多用、自律トランザクション相当のフロー。
      ******************************************************************
       IDENTIFICATION DIVISION.
       PROGRAM-ID. PRDCLOSE.

       DATA DIVISION.
       WORKING-STORAGE SECTION.
           COPY COMMON.

       01  WS-SQLCA.
           EXEC SQL INCLUDE SQLCA END-EXEC.

       01  WS-DLI-PCB-LIST.
           05  WS-IO-PCB              PIC X(100).
           05  WS-INV-PCB             PIC X(100).
           05  WS-GL-PCB              PIC X(100).

       01  WS-DLI-CALL-FUNCTIONS.
           05  WS-GU                  PIC X(4) VALUE 'GU  '.
           05  WS-GN                  PIC X(4) VALUE 'GN  '.
           05  WS-ISRT                PIC X(4) VALUE 'ISRT'.
           05  WS-REPL                PIC X(4) VALUE 'REPL'.

       01  WS-INVENTORY-SEGMENT.
           05  WS-INV-SEG-KEY         PIC X(10).
           05  WS-INV-SEG-QTY         PIC 9(9) COMP-3.
           05  WS-INV-SEG-VALUE       PIC S9(13)V99 COMP-3.

       01  WS-GL-SEGMENT.
           05  WS-GL-ACCOUNT          PIC X(8).
           05  WS-GL-PERIOD           PIC 9(6).
           05  WS-GL-DEBIT            PIC S9(13)V99 COMP-3.
           05  WS-GL-CREDIT           PIC S9(13)V99 COMP-3.

       01  WS-TXN-FLAG                PIC X VALUE 'I'.
           88  TXN-INITIAL                VALUE 'I'.
           88  TXN-COMMITTED              VALUE 'C'.
           88  TXN-ROLLED-BACK            VALUE 'R'.

       01  WS-ALTER-TARGET            PIC X(8) VALUE 'NORMAL  '.

       PROCEDURE DIVISION.
       MAIN-PARA.
           PERFORM INIT-PARA THRU INIT-EXIT.
           PERFORM PROCESS-CLOSE THRU PROCESS-EXIT.
           PERFORM FINALIZE-PARA THRU FINALIZE-EXIT.
           PERFORM RETURN-TO-CICS.
           GOBACK.

       INIT-PARA.
           ACCEPT WS-CURRENT-DATE FROM DATE YYYYMMDD.
           MOVE WS-FISCAL-PERIOD TO WS-GL-PERIOD.

           ALTER POST-COMMIT-BRANCH TO PROCEED TO NORMAL-COMMIT.

           EXEC CICS GETMAIN
               SET(ADDRESS OF WS-DLI-PCB-LIST)
               LENGTH(LENGTH OF WS-DLI-PCB-LIST)
               INITIMG(LOW-VALUES)
           END-EXEC.

       INIT-EXIT.
           EXIT.

       PROCESS-CLOSE.
           PERFORM READ-INVENTORY THRU READ-INV-EXIT
               UNTIL WS-INV-SEG-KEY = HIGH-VALUES.

           IF WS-ERR-NONE = 0
               PERFORM POST-TO-GL THRU POST-GL-EXIT
           ELSE
               MOVE 'ABNORMAL' TO WS-ALTER-TARGET
               ALTER POST-COMMIT-BRANCH TO PROCEED TO ABNORMAL-COMMIT
               GO TO PROCESS-EXIT.

       READ-INVENTORY.
           CALL 'CBLTDLI' USING WS-GN
                                 WS-INV-PCB
                                 WS-INVENTORY-SEGMENT.

           IF WS-INV-SEG-KEY = HIGH-VALUES
               GO TO READ-INV-EXIT.

           COMPUTE WS-INV-SEG-VALUE =
               WS-INV-SEG-QTY * 100.

       READ-INV-EXIT.
           EXIT.

       POST-TO-GL.
           MOVE 'INV-CTRL' TO WS-GL-ACCOUNT.
           MOVE WS-INV-SEG-VALUE TO WS-GL-DEBIT.

           CALL 'CBLTDLI' USING WS-ISRT
                                 WS-GL-PCB
                                 WS-GL-SEGMENT.

           EXEC SQL
               INSERT INTO GL_JOURNAL
                   (ACCOUNT, PERIOD, DEBIT, CREDIT, POSTED_DATE)
               VALUES
                   (:WS-GL-ACCOUNT, :WS-GL-PERIOD,
                    :WS-GL-DEBIT, :WS-GL-CREDIT, :WS-CURRENT-DATE)
           END-EXEC.

       POST-GL-EXIT.
           EXIT.

       PROCESS-EXIT.
           EXIT.

       FINALIZE-PARA.
       POST-COMMIT-BRANCH.
           GO TO NORMAL-COMMIT.

       NORMAL-COMMIT.
           EXEC CICS SYNCPOINT END-EXEC.
           SET TXN-COMMITTED TO TRUE.
           GO TO FINALIZE-EXIT.

       ABNORMAL-COMMIT.
           EXEC CICS SYNCPOINT ROLLBACK END-EXEC.
           SET TXN-ROLLED-BACK TO TRUE.

       FINALIZE-EXIT.
           EXIT.

       RETURN-TO-CICS.
           EXEC CICS RETURN END-EXEC.

       END PROGRAM PRDCLOSE.
