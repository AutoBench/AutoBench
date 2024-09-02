module top_module (
	input clk,
	input d,
	input ar,
	output logic q
);

	always@(posedge clk) begin // Removed "ar" from sensitivity list
		if (ar)
			q <= 0;
		else
			q <= d;
	end

endmodule
