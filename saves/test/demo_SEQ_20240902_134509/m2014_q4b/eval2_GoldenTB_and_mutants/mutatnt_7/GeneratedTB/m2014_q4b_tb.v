`timescale 1ns / 1ps
module testbench;
reg  clk;
reg  d;
reg  ar;
wire  q;

integer file, scenario;
// DUT instantiation
top_module DUT (
    .clk(clk),
    .d(d),
    .ar(ar),
    .q(q)
);
// Clock generation
initial begin
    clk = 0;
    forever #5 clk = ~clk;
end

initial begin
    file = $fopen("TBout.txt", "w");
end
// Scenario Based Test
initial begin
    // Scenario 1
    scenario = 1;
    ar = 1; d = 0;
    $fdisplay(file, "scenario: %d, clk = %d, d = %d, ar = %d, q = %d", scenario, clk, d, ar, q); #10; 
    repeat(5) begin
        $fdisplay(file, "[check]scenario: %d, clk = %d, d = %d, ar = %d, q = %d", scenario, clk, d, ar, q);
        #10;
    end
    ar = 0;
    $fdisplay(file, "scenario: %d, clk = %d, d = %d, ar = %d, q = %d", scenario, clk, d, ar, q); #10; 
    repeat(5) begin
        $fdisplay(file, "[check]scenario: %d, clk = %d, d = %d, ar = %d, q = %d", scenario, clk, d, ar, q);
        #10;
    end

    // Scenario 2
    scenario = 2;
    ar = 0; d = 0;
    $fdisplay(file, "scenario: %d, clk = %d, d = %d, ar = %d, q = %d", scenario, clk, d, ar, q); #10; 
    repeat(2) begin
        $fdisplay(file, "[check]scenario: %d, clk = %d, d = %d, ar = %d, q = %d", scenario, clk, d, ar, q);
        #10;
    end
    d = 1;
    $fdisplay(file, "scenario: %d, clk = %d, d = %d, ar = %d, q = %d", scenario, clk, d, ar, q); #10; 
    repeat(3) begin
        $fdisplay(file, "[check]scenario: %d, clk = %d, d = %d, ar = %d, q = %d", scenario, clk, d, ar, q);
        #10;
    end
    d = 0;
    $fdisplay(file, "scenario: %d, clk = %d, d = %d, ar = %d, q = %d", scenario, clk, d, ar, q); #10; 

    // Scenario 3
    scenario = 3;
    d = 1; ar = 0;
    $fdisplay(file, "scenario: %d, clk = %d, d = %d, ar = %d, q = %d", scenario, clk, d, ar, q); #10; 
    $fdisplay(file, "[check]scenario: %d, clk = %d, d = %d, ar = %d, q = %d", scenario, clk, d, ar, q);
    #10;
    ar = 1;
    $fdisplay(file, "scenario: %d, clk = %d, d = %d, ar = %d, q = %d", scenario, clk, d, ar, q); #10; 
    $fdisplay(file, "[check]scenario: %d, clk = %d, d = %d, ar = %d, q = %d", scenario, clk, d, ar, q);
    #10;
    ar = 0;
    $fdisplay(file, "scenario: %d, clk = %d, d = %d, ar = %d, q = %d", scenario, clk, d, ar, q); #10; 
    repeat(3) begin
        $fdisplay(file, "[check]scenario: %d, clk = %d, d = %d, ar = %d, q = %d", scenario, clk, d, ar, q);
        #10;
    end

    // Scenario 4
    scenario = 4;
    ar = 0; d = 0;
    repeat(10) begin
        d = ~d;
        $fdisplay(file, "scenario: %d, clk = %d, d = %d, ar = %d, q = %d", scenario, clk, d, ar, q); #10; 
        $fdisplay(file, "[check]scenario: %d, clk = %d, d = %d, ar = %d, q = %d", scenario, clk, d, ar, q);
        #10;
    end

    // Scenario 5
    scenario = 5;
    ar = 0; d = 1;
    $fdisplay(file, "scenario: %d, clk = %d, d = %d, ar = %d, q = %d", scenario, clk, d, ar, q); #10; 
    repeat(3) begin $fdisplay(file, "[check]scenario: %d, clk = %d, d = %d, ar = %d, q = %d", scenario, clk, d, ar, q); #10; end
    $fdisplay(file, "scenario: %d, clk = %d, d = %d, ar = %d, q = %d", scenario, clk, d, ar, q); #10.5;  // clock glitch
    $fdisplay(file, "[check]scenario: %d, clk = %d, d = %d, ar = %d, q = %d", scenario, clk, d, ar, q);
    #10;  // remaining half clock
    repeat(2) begin $fdisplay(file, "[check]scenario: %d, clk = %d, d = %d, ar = %d, q = %d", scenario, clk, d, ar, q); #10; end

    // Scenario 6
    scenario = 6;
    ar = 1; d = 1;
    $fdisplay(file, "scenario: %d, clk = %d, d = %d, ar = %d, q = %d", scenario, clk, d, ar, q); #10; 
    repeat(2) begin
        $fdisplay(file, "[check]scenario: %d, clk = %d, d = %d, ar = %d, q = %d", scenario, clk, d, ar, q);
        #10;
    end
    ar = 0;
    d = 0;
    $fdisplay(file, "scenario: %d, clk = %d, d = %d, ar = %d, q = %d", scenario, clk, d, ar, q); #10; 
    repeat(4) begin
        $fdisplay(file, "[check]scenario: %d, clk = %d, d = %d, ar = %d, q = %d", scenario, clk, d, ar, q);
        #10;
    end

    // Scenario 7
    scenario = 7;
    ar = 1; d = 0;
    $fdisplay(file, "scenario: %d, clk = %d, d = %d, ar = %d, q = %d", scenario, clk, d, ar, q); #10; 
    $fdisplay(file, "[check]scenario: %d, clk = %d, d = %d, ar = %d, q = %d", scenario, clk, d, ar, q);
    #10; $fdisplay(file, "scenario: %d, clk = %d, d = %d, ar = %d, q = %d", scenario, clk, d, ar, q); #10; // midway falling edge
    ar = 0;
    $fdisplay(file, "scenario: %d, clk = %d, d = %d, ar = %d, q = %d", scenario, clk, d, ar, q); #10; 
    repeat(3) begin
        $fdisplay(file, "[check]scenario: %d, clk = %d, d = %d, ar = %d, q = %d", scenario, clk, d, ar, q);
        #10;
    end

    $fclose(file);
    $finish;
end

endmodule
