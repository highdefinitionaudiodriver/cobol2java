      ******************************************************************
      * Sample COPYBOOK — Customer Record (CC0 / public domain)
      * 複数プログラムから COPY で取り込まれる共通レイアウト。
      ******************************************************************
       01  CUSTOMER-RECORD.
           05  CUST-ID-K              PIC 9(8).
           05  CUST-NAME-K            PIC X(40).
           05  CUST-KANA-K            PIC X(40).
           05  CUST-POSTAL-K          PIC X(8).
           05  CUST-ADDRESS-K         PIC X(80).
           05  CUST-PHONE-K           PIC X(15).
           05  CUST-EMAIL-K           PIC X(60).
           05  CUST-CREDIT-LIMIT-K    PIC 9(9)V99 COMP-3.
           05  CUST-BALANCE-K         PIC S9(11)V99 COMP-3.
           05  CUST-STATUS-K          PIC X.
               88  CUST-ACTIVE-K           VALUE 'A'.
               88  CUST-SUSPENDED-K        VALUE 'S'.
               88  CUST-CLOSED-K           VALUE 'C'.
           05  CUST-REG-DATE-K        PIC 9(8).
           05  CUST-LAST-ORDER-K      PIC 9(8).
           05  CUST-PAYMENT-TERM-K    PIC 9(3).
           05  FILLER                 PIC X(20).
