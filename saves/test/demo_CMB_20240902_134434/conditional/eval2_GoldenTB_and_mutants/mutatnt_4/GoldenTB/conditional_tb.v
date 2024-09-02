`timescale 1 ps/1 ps
`define OK 12
`define INCORRECT 13
module reference_module (
	input [7:0] a,
	input [7:0] b,
	input [7:0] c,
	input [7:0] d,
	output reg [7:0] min
);

	always_comb begin
		min = a;
		if (min > b) min = b;
		if (min > c) min = c;
		if (min > d) min = d;
	end
	
endmodule


module stimulus_gen (
	input clk,
	output logic [7:0] a, b, c, d,
	output reg[511:0] wavedrom_title,
	output reg wavedrom_enable
);

// Add two ports to module stimulus_gen:
//    output [511:0] wavedrom_title
//    output reg wavedrom_enable

	task wavedrom_start(input[511:0] title = "");
	endtask
	
	task wavedrom_stop;
		#1;
	endtask	


 	initial begin
 		{a,b,c,d} <= {8'h1, 8'h2, 8'h3, 8'h4};
 		@(negedge clk);
 		wavedrom_start();
	 		@(posedge clk) {a,b,c,d} <= {8'h1, 8'h2, 8'h3, 8'h4};
	 		@(posedge clk) {a,b,c,d} <= {8'h11, 8'h2, 8'h3, 8'h4};
	 		@(posedge clk) {a,b,c,d} <= {8'h11, 8'h12, 8'h3, 8'h4};
	 		@(posedge clk) {a,b,c,d} <= {8'h11, 8'h12, 8'h13, 8'h4};
	 		@(posedge clk) {a,b,c,d} <= {8'h11, 8'h12, 8'h13, 8'h14};
 		@(negedge clk);
 		wavedrom_stop();
		repeat(100) @(posedge clk, negedge clk)
			{a,b,c,d} <= $random;
		$finish;
	end
	
endmodule

module tb();

	typedef struct packed {
		int errors;
		int errortime;
		int errors_min;
		int errortime_min;

		int clocks;
	} stats;
	
	stats stats1;
	
	
	wire[511:0] wavedrom_title;
	wire wavedrom_enable;
	int wavedrom_hide_after_time;
	
	reg clk=0;
	initial forever
		#5 clk = ~clk;

	logic [7:0] a;
	logic [7:0] b;
	logic [7:0] c;
	logic [7:0] d;
	logic [7:0] min_ref;
	logic [7:0] min_dut;

	initial begin 
		$dumpfile("wave.vcd");
		$dumpvars(1, stim1.clk, tb_mismatch ,a,b,c,d,min_ref,min_dut );
	end


	wire tb_match;		// Verification
	wire tb_mismatch = ~tb_match;
	
	stimulus_gen stim1 (
		.clk,
		.* ,
		.a,
		.b,
		.c,
		.d );
	reference_module good1 (
		.a,
		.b,
		.c,
		.d,
		.min(min_ref) );
		
	top_module top_module1 (
		.a,
		.b,
		.c,
		.d,
		.min(min_dut) );

	
	bit strobe = 0;
	task wait_for_end_of_timestep;
		repeat(5) begin
			strobe <= !strobe;  // Try to delay until the very end of the time step.
			@(strobe);
		end
	endtask	

	
	final begin
		if (stats1.errors_min) $display("Hint: Output '%s' has %0d mismatches. First mismatch occurred at time %0d.", "min", stats1.errors_min, stats1.errortime_min);
		else $display("Hint: Output '%s' has no mismatches.", "min");

		$display("Hint: Total mismatched samples is %1d out of %1d samples\n", stats1.errors, stats1.clocks);
		$display("Simulation finished at %0d ps", $time);
		$display("Mismatches: %1d in %1d samples", stats1.errors, stats1.clocks);
	end
	
	// Verification: XORs on the right makes any X in good_vector match anything, but X in dut_vector will only match X.
	assign tb_match = ( { min_ref } === ( { min_ref } ^ { min_dut } ^ { min_ref } ) );
	// Use explicit sensitivity list here. @(*) causes NetProc::nex_input() to be called when trying to compute
	// the sensitivity list of the @(strobe) process, which isn't implemented.
	always @(posedge clk, negedge clk) begin

		stats1.clocks++;
		if (!tb_match) begin
			if (stats1.errors == 0) stats1.errortime = $time;
			stats1.errors++;
		end
		if (min_ref !== ( min_ref ^ min_dut ^ min_ref ))
		begin if (stats1.errors_min == 0) stats1.errortime_min = $time;
			stats1.errors_min = stats1.errors_min+1'b1; end

	end
endmodule
