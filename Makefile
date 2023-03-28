OUT_DIR = build

exec:
	mkdir -p $(OUT_DIR)
	cmake . -B $(OUT_DIR)
	$(MAKE) -C $(OUT_DIR)
	cd $(OUT_DIR) && ./cartaxi_bot
clean:
	rm -rf build