#ifndef NIOS2_H
#define NIOS2_H

#include <stdio.h>
#include <stdint.h>
#include <unistd.h>
#include <sys/types.h>
#include <sys/socket.h>
#include <netinet/in.h>
#include <arpa/inet.h>
#include <string.h>
void *memmem(const void *haystack, size_t haystacklen,
             const void *needle, size_t needlelen);


// Yeah, Moodle is dumb. Things submitted by the user in comments (from the box) get \r\n
// line endings. Things outside don't.
#define ASM_START_SENTINAL  "/* ******* DO NOT MODIFY THIS LINE *******\n"
#define ASM_END_SENTINAL    "********* DO NOT MODIFY THIS LINE ******* */\n"
//#define PROGRAM_FNAME       "prog.c"
#define PROGRAM_FNAME       "__tester__.c"
#define ASM_FNAME           "output.s"
#define MACHINE_FNAME       "output.o"

ssize_t getline(char **lineptr, size_t *n, FILE *stream);


/* Reads prog.c, gets between the lines that have DO NOT MODIFY THIS LINE
 * Returns a malloc'd pointer to the assembly
 */
void get_asm() {

    FILE *fp;
    FILE *out;
    ssize_t read;
    size_t len;
    char *line = NULL;

    fp = fopen(PROGRAM_FNAME, "r");
    if (fp == NULL) {
        printf("Failure to read %s", PROGRAM_FNAME);
        perror("fopen");
        exit(-1);
    }

    out = fopen(ASM_FNAME, "w");
    if (out == NULL) {
        printf("Failure to open %s", ASM_FNAME);
        perror("fopen");
        exit(-1);
    }

    bool in_asm = false;
    while ((read = getline(&line, &len, fp)) != -1) {
        if (strncmp(ASM_START_SENTINAL, line, len)==0) {
            in_asm = true;
        } else if (strncmp(ASM_END_SENTINAL, line, len)==0) {
            in_asm = false;
        } else if (in_asm) {
            int ll = strlen(line);
            if (line[ll-2] == '\r' && line[ll-1] == '\n') {
                fwrite(line, 1, strlen(line)-2, out);   // -2 to get rid of \r\n
                fwrite("\n", 1, 1, out);                // put back \n
            } else {
                fwrite(line, 1, strlen(line), out);
            }
        }
    }
    fclose(out);
}

// Returns 1 on error (check errno, probably)
// and 0 on success (sent all length bytes)
int sendall(int socket, void *buffer, size_t length)
{
    char *ptr = (char*) buffer;
    while (length > 0) {
        int i = send(socket, ptr, length, 0);
        if (i < 1) {
            return 1;
        }
        ptr += i;
        length -= i;
    }
    return 0;
}

// Mallocs/reallocs *buffer
size_t recvall(int socket, char **buffer)
{
    *buffer = NULL;
    size_t tot_size = 0;
    while (1) {
        *buffer = realloc(*buffer, tot_size + 1500);
        char *p = *buffer;
        ssize_t r = recv(socket, &p[tot_size], 1500, 0);
        if (r < 0) {
            perror("recv");
            exit(-1);
        } else if (r == 0) {
            return tot_size;
        }
        tot_size += r;
    }
}

char *getfile(char *fname)
{
    FILE *fp = fopen(fname, "r");

    fseek(fp, 0L, SEEK_END); 
    size_t sz = ftell(fp);
    char *buf = malloc(sz);
    rewind(fp);

    fread(buf, 1, sz, fp);
    return buf;
}

void print_hex(unsigned char *buf, size_t len)
{
    int i;
    for (i=0; i<len; i++)
    {
        if ((i%16)==0) {
            printf("\n");
        }
        printf("%02x", buf[i]);
    }
    printf("\n");
}


/* Reads output.s, prints response
 */
void remote_autograde(char *eid, char uid)
{

    // Write assembly file (output.s)
    get_asm();

    // Read output.s
    char *str_asm = getfile(ASM_FNAME);

    int s = socket(AF_INET, SOCK_STREAM, 0);
    if (s < 0) {
        perror("socket");
        exit(-1);
    }


    int i;
    for (i=0; i<5; i++) {   // retry up to 5 times

        // ecen3350.rocks
        struct sockaddr_in dst;
        dst.sin_family = AF_INET;
        dst.sin_port = htons(80);
        inet_pton(AF_INET, "18.234.115.5", &dst.sin_addr);
        if (connect(s, (struct sockaddr*)&dst, sizeof(dst)) < 0) {
            perror("connect");
            exit(-1);
        }

        //print_hex((unsigned char*)str_asm, strlen(str_asm));

        char *post_hdr_template = "POST /nios2/examples.moodle/%s/%c HTTP/1.1\r\nHost: ecen3350.rocks\r\nContent-Type: multipart/form-data; boundary=---------------------------hGq7UiBbThSgROYS\r\nConnection: Close\r\nContent-Length: %d\r\n\r\n";
        char *post_body_template = "-----------------------------hGq7UiBbThSgROYS\r\nContent-Disposition: form-data; name=\"asm\"\r\n\r\n%s\r\n-----------------------------hGq7UiBbThSgROYS\r\n";

        // Construct body and header
        size_t body_len = strlen(post_body_template) + strlen(str_asm) - 2; // -2 for replaced %s with str_asm
        char *post_body = malloc(body_len);
        size_t hdr_len = strlen(post_hdr_template) + strlen(eid) + 10;
                                                        // conservative upper bound,
                                                        // +10 should be floor(log10(body_len)) + 1(uid)
        char *post_hdr  = malloc(hdr_len);

        snprintf(post_body, body_len, post_body_template, str_asm);
        snprintf(post_hdr, hdr_len, post_hdr_template, eid, uid, strlen(post_body));

        // Send HTTP Request/body
        sendall(s, post_hdr, strlen(post_hdr));
        sendall(s, post_body, strlen(post_body));

        // Receive HTTP Response
        char *response;
        size_t resp_len = recvall(s, &response);

        char *result = (char *)memmem(response, resp_len, "\r\n\r\n", 4);

        if (result != NULL) {
            char *resp = &result[4];
            if (strstr(resp, "<title>Error: 500 Internal Server Error</title>") != NULL) {
                // Some kind of internal error...retry?
                if (i==4) {
                    // Failed 5 times, just give up
                    printf("%s", resp);
                    return;
                }
                // Sleep for 1 sec
                sleep(1);
                continue;
            } else {
                printf("%s", resp);
                return;
            }
        } else {
            printf("Error: could not find line breaks in HTTP response: %s\n", response);
            return;
        }
    }
}

#endif
