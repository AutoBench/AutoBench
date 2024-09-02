module top_module (
	input clk,
	input d,
	input ar,
	output logic q
);

	always@(posedge clk or posedge ar) begin
		if (ar)
			q <= 1; // Changed reset value to 1 instead of 0
		else
			q <= d;
	end

endmodule
