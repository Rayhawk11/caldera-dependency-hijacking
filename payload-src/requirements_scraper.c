#include <stdio.h>
#include <stdlib.h>
#include <string.h>

int main(int argc, const char *argv[]) {
	if(argc == 1) return -1;
	const char *result_file = argv[1];
	const char *search_path = "./";
	if(argc >= 3) {
		search_path = argv[2];
	}
	char buffer[1024];
	size_t search_path_len = strlen(search_path);
	strcpy(buffer, "find ");
	strcat(buffer, search_path);
	strcat(buffer, " -name requirements.txt");
	FILE *pipe = popen(buffer, "r");
	ssize_t result;
	char *line = NULL;
	size_t n = 0;
	ssize_t line_length = 0;
	sprintf(buffer, "touch %s", result_file);
	system(buffer);
	sprintf(buffer, "> %s", result_file);
	system(buffer);
	while((line_length = getline(&line, &n, pipe)) != -1) {
		line[line_length - 1] = 0;
		sprintf(buffer, "cat %s >> %s", line, result_file);
		system(buffer);
	}
	pclose(pipe);
	free(line);
}
