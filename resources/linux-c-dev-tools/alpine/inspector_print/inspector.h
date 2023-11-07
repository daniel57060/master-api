#ifndef INSPECTOR_H
#define INSPECTOR_H

#include <errno.h>
#include <stdarg.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <sys/stat.h>
#include <sys/time.h>
#include <sys/wait.h>
#include <unistd.h>
#include <stdint.h>

#define BUFFER_SIZE 1024
#define BUFFER_X 256
#define PAYLOAD_SIZE (BUFFER_SIZE - BUFFER_X)
#define VALUE_SIZE 256

char directory[64] = {0};
FILE *fd = NULL;
int fork_count = 0;
int depth = 0;
int in_fork = 0;

// public
// TOOD: void inspector_program_start(char *function_name, int line);
// TODO: void inspector_program_end(char *function_name, int line, int status);
// TODO: Remove Inspector_function_enter() and Inspector_function_exit()?
void inspector_function_enter(char *function_name, int line);
void inspector_function_exit(char *function_name, int line);
void inspector_function_call(char *function_caller_name, int line, char *function_name);
void inspector_variable_declare(char *function_name, int line, char *type, char *variable_name);
void inspector_variable_assign(char *function_name, int line, char *type, char *variable_name, void *value);
void inspector_exit(char *function_name, int line, int status);
int inspector_condition(char *function_name, int line, char *cause, int value, char *expression);
int inspector_printf(char *function_name, int line, const char *format, ...);
int inspector_fork(char *function_name, int line);
int inspector_wait(char *function_name, int line, int *out_status);
int inspector_waitpid(char *function_name, int line, int wait_pid, int *out_status, int options);

#endif // INSPECTOR_H

#ifdef INSPECTOR_IMPLEMENTATION

void __ensure_directory(char *directory_name)
{
    struct stat st = {0};
    if (stat(directory_name, &st) == -1)
    {
        mkdir(directory_name, 0700);
    }
}

void __open_inspector_file()
{
    int pid = getpid();
    char filename[100] = {0};
    sprintf(filename, "%s/%d.json", directory, pid);
    fd = fopen(filename, "w");
    if (fd == NULL)
    {
        printf("Error opening file: %s!\n", filename);
        printf("%s\n", strerror(errno));
        exit(1);
    }
}

void __escape_string(char *str, char *buffer)
{
    while (*str)
    {
        if (*str == '\n')
        {
            *buffer = '\\';
            buffer++;
            *buffer = 'n';
            buffer++;
            str++;
        }
        else if (*str == '\t')
        {
            *buffer = '\\';
            buffer++;
            *buffer = 't';
            buffer++;
            str++;
        }
        else
        {
            *buffer = *str;
            buffer++;
            str++;
        }
    }
}

void __suround_string(char *str, char *buffer)
{
    int n = strlen(str);
    for (int i = n; i > 0; i--)
    {
        buffer[i] = str[i - 1];
    }
    buffer[0] = '"';
    buffer[n + 1] = '"';
}

int64_t __current_time()
{
#if 1
    // https://stackoverflow.com/questions/5833094/get-a-timestamp-in-c-in-microseconds
    struct timeval tv;
    gettimeofday(&tv, NULL);
    return tv.tv_sec * (int64_t)1000000 + tv.tv_usec;
#else
    // https://stackoverflow.com/questions/5833094/get-a-timestamp-in-c-in-microseconds
    struct timeval time;
    gettimeofday(&time, NULL);
    int64_t s1 = (int64_t)(time.tv_sec) * 1000;
    int64_t s2 = (time.tv_usec / 1000);
    return s1 + s2;
#endif
}

void __inspect_json(FILE *fd, char *type, char *function_name, int line, char *payload)
{
    if (in_fork)
    {
        return;
    }
    int parent_pid = getppid();
    int pid = getpid();
    int64_t time = __current_time();
    fprintf(fd, "{ \"time\": %ld, \"depth\": %d, \"pid\": %d, \"parent_pid\": %d, \"function\": \"%s\", \"type\": \"%s\", \"line\": %d, \"payload\": %s }\n", time, depth, pid, parent_pid, function_name, type, line, payload);
    fflush(fd);
}

void __inspect_string(FILE *fd, char *type, char *function_name, int line, char *payload)
{
    char buffer[768] = {0};
    __suround_string(payload, buffer);
    __inspect_json(fd, type, function_name, line, buffer);
}

void __inspector_fork_enter(char *function_name, int line)
{
    __inspect_string(fd, "fork_enter", function_name, line, "");
}

void __inspector_fork_exit(char *function_name, int child_pid, int line)
{
    if (child_pid == 0) /* child */
    {
        fork_count = 0;
        __open_inspector_file();
        depth += 1;
    }
    else /* parent */
    {
        fork_count++;
    }
    char payload[PAYLOAD_SIZE] = {0};
    sprintf(payload, "%d", child_pid);
    __inspect_json(fd, "fork_exit", function_name, line, payload);
}

void __inspector_printf(char *function_name, int line, char *data)
{
    char payload[PAYLOAD_SIZE] = {0};
    __escape_string(data, payload);
    __inspect_string(fd, "printf", function_name, line, payload);
}

void __inspector_end()
{
    if (fork_count > 0)
    {
        for (int i = 0; i < fork_count; i++)
        {
            int status;
            wait(&status);
        }
    }
    fclose(fd);
    fd = NULL;
}

void inspector_function_enter(char *function_name, int line)
{

    if (strcmp(function_name, "main") == 0)
    {
        if (directory[0] == 0)
        {
            sprintf(directory, "outs");
            __ensure_directory(directory);
        }

        __open_inspector_file();
    }
    __inspect_string(fd, "function_enter", function_name, line, "");
}

void inspector_function_exit(char *function_name, int line)
{
    __inspect_string(fd, "function_exit", function_name, line, "");
    if (strcmp(function_name, "main") == 0)
    {
        __inspector_end();
    }
}

void inspector_function_call(char *function_caller_name, int line, char *function_name)
{
    char payload[PAYLOAD_SIZE] = {0};
    sprintf(payload, "{ \"function\": \"%s\" }", function_name);
    __inspect_json(fd, "function_call", function_caller_name, line, payload);
}

void inspector_variable_declare(char *function_name, int line, char *type, char *variable_name)
{
    char payload[PAYLOAD_SIZE] = {0};
    sprintf(payload, "{ \"type\": \"%s\", \"name\": \"%s\" }", type, variable_name);
    __inspect_json(fd, "variable_declare", function_name, line, payload);
}

void inspector_variable_assign(char *function_name, int line, char *type, char *variable_name, void *value)
{
    char value_str[VALUE_SIZE] = {0};
    strcat(value_str, "null");
    if (strcmp(type, "int") == 0)
    {
        sprintf(value_str, "%d", *((int *)value));
    }
    else if (strcmp(type, "pid_t") == 0)
    {
        sprintf(value_str, "%d", *((int *)value));
    }
    char payload[PAYLOAD_SIZE] = {0};
    sprintf(payload, "{ \"type\": \"%s\", \"name\": \"%s\", \"value\": %s }", type, variable_name, value_str);
    __inspect_json(fd, "variable_assign", function_name, line, payload);
}

int inspector_condition(char *function_name, int line, char *cause, int value, char *expression)
{
    char payload[PAYLOAD_SIZE] = {0};
    sprintf(payload, "{ \"cause\": \"%s\", \"value\": %d, \"expression\": \"%s\" }", cause, value, expression);
    __inspect_json(fd, "condition", function_name, line, payload);
    return value;
}

int inspector_printf(char *function_name, int line, const char *format, ...)
{
    char buffer[BUFFER_SIZE] = {0};
    va_list args;
    va_start(args, format);
    vsprintf(buffer, format, args);
    va_end(args);
    __inspector_printf(function_name, line, buffer);
    return printf("%s", buffer);
}

int inspector_fork(char *function_name, int line)
{
    __inspector_fork_enter(function_name, line);
    FILE *fd_tmp = fd;
    in_fork = 1;
    int pid = fork();
    in_fork = 0;
    __inspector_fork_exit(function_name, pid, line);
    return pid;
}

void inspector_exit(char *function_name, int line, int status)
{
    __inspect_string(fd, "exit", function_name, line, "");
    __inspector_end();
    exit(status);
}

int inspector_wait(char *function_name, int line, int *out_status)
{
    int status;
    char payload[PAYLOAD_SIZE] = {0};
    int pid = wait(&status);
    sprintf(payload, "{ \"pid\": %d, \"status\": %d }", pid, status);
    __inspect_json(fd, "wait", function_name, line, payload);
    if (out_status != NULL)
    {
        *out_status = status;
    }
    fork_count--;
    return pid;
}

int inspector_waitpid(char *function_name, int line, int wait_pid, int *out_status, int options)
{
    int status;
    char payload[PAYLOAD_SIZE] = {0};
    int pid = waitpid(wait_pid, &status, options);
    sprintf(payload, "{ \"pid\": %d, \"status\": %d }", pid, status);
    __inspect_json(fd, "waitpid", function_name, line, payload);
    if (out_status != NULL)
    {
        *out_status = status;
    }
    fork_count--;
    return pid;
}

#endif
