`timescale 1ns / 1ps

module testbench;
    reg [7:0] a, b, c, d;
    wire [7:0] min;
    integer file;

    // Instantiate the Device Under Test (DUT)
    top_module DUT (
        .a(a),
        .b(b),
        .c(c),
        .d(d),
        .min(min)
    );

    initial begin
        // Open the file for output
        file = $fopen("TBout.txt", "w");

        // Scenario 1: All inputs are equal
        a = 127; b = 127; c = 127; d = 127;
        #10; // Wait for the output to stabilize
        $fdisplay(file, "scenario: 1, a = %d, b = %d, c = %d, d = %d, min = %d", a, b, c, d, min);

        // Scenario 2: Gradual increase
        a = 10; b = 20; c = 30; d = 40;
        #10;
        $fdisplay(file, "scenario: 2, a = %d, b = %d, c = %d, d = %d, min = %d", a, b, c, d, min);

        // Scenario 3: Inverse gradual increase
        a = 40; b = 30; c = 20; d = 10;
        #10;
        $fdisplay(file, "scenario: 3, a = %d, b = %d, c = %d, d = %d, min = %d", a, b, c, d, min);

        // Scenario 4: Max boundary conditions
        a = 255; b = 255; c = 255; d = 255;
        #10;
        $fdisplay(file, "scenario: 4, a = %d, b = %d, c = %d, d = %d, min = %d", a, b, c, d, min);

        // Scenario 5: Min boundary condition
        a = 255; b = 255; c = 255; d = 0;
        #10;
        $fdisplay(file, "scenario: 5, a = %d, b = %d, c = %d, d = %d, min = %d", a, b, c, d, min);

        // Scenario 6: Distinct values
        a = 67; b = 89; c = 12; d = 234;
        #10;
        $fdisplay(file, "scenario: 6, a = %d, b = %d, c = %d, d = %d, min = %d", a, b, c, d, min);

        // Scenario 7: Same high & low with one distinct
        a = 255; b = 255; c = 5; d = 5;
        #10;
        $fdisplay(file, "scenario: 7, a = %d, b = %d, c = %d, d = %d, min = %d", a, b, c, d, min);

        // Scenario 8: Varying middle range values
        a = 100; b = 120; c = 110; d = 130;
        #10;
        $fdisplay(file, "scenario: 8, a = %d, b = %d, c = %d, d = %d, min = %d", a, b, c, d, min);

        // Scenario 9: Alternating same values
        a = 56; b = 78; c = 56; d = 78;
        #10;
        $fdisplay(file, "scenario: 9, a = %d, b = %d, c = %d, d = %d, min = %d", a, b, c, d, min);

        // Scenario 10: Single minimal value
        a = 220; b = 200; c = 255; d = 1;
        #10;
        $fdisplay(file, "scenario: 10, a = %d, b = %d, c = %d, d = %d, min = %d", a, b, c, d, min);

        // Close the file
        $fclose(file);

        // Finish the simulation
        $finish;
    end

endmodule
