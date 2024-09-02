module top_module (
	input clk,
	input d,
	input ar,
	output logic q
);

	always@(posedge clk or negedge ar) begin // Changed sensitivity to negedge of "ar" instead of posedge
		if (ar)
			q <= 0;
		else
			q <= d;
	end

endmodule
