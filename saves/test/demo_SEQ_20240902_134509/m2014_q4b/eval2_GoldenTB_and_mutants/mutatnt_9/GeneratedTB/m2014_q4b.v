module top_module (
	input clk,
	input d,
	input ar,
	output logic q
);

	always@(posedge clk or posedge ar) begin
		// Added dummy logic that does not affect functionality
		if (ar)
			q <= 0;
		else if (!ar)
			q <= d;
		else
			q <= d; // Unnecessary else case
	end

endmodule
