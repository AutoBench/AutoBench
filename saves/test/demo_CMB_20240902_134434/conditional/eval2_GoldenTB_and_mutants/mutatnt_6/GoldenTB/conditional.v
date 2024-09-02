module top_module (
	input [7:0] a,
	input [7:0] b,
	input [7:0] c,
	input [7:0] d,
	output reg [7:0] min
);

	always_comb begin
		min = a;
		if (min > b) min = b;
		// Removed c comparison
		if (min > d) min = d;
	end
	
endmodule
