module top_module (
	input [7:0] a,
	input [7:0] b,
	input [7:0] c,
	input [7:0] d,
	output reg [7:0] min
);

	always_comb begin
		min = b; // Change: Initializing min with b instead of a
		if (min > a) min = a;
		if (min > c) min = c;
		if (min > d) min = d;
	end
	
endmodule
