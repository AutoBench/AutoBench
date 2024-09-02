module top_module (
	input clk,
	input d,
	input ar,
	output logic q
);

	always@(posedge clk or posedge ar) begin
		if (ar)
			q <= 0;
		else
			q <= d & ar; // Changed assignment to "d" AND "ar"
	end

endmodule
