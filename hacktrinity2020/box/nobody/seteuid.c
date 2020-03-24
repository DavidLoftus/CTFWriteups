#include <unistd.h>

int main(int argc, char** argv) {
	seteuid(0);
	return execvp(argv[1], &argv[1]);
}
