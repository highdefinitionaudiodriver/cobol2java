package com.migrated;

import java.util.Scanner;

/**
 * Main class migrated from COBOL program: HELLO
 */
public class Hello {


    public Hello() {
    }

    /**
     * Migrated from COBOL paragraph: MAIN
     */
    public void main() {
        System.out.println("Hello World");
        System.exit(0);
    }

    public static void main(String[] args) {
        Hello program = new Hello();
        program.main();
    }

}