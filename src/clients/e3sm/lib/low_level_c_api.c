#include <curl/curl.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

#define MAX_URL_SIZE 2048

/**
 * Function to create a session on the server by making a POST request with JSON data.
 * @param base_url Base URL of the server
 * @param source_model_ID ID of the source model
 * @param destination_model_ID ID of the destination model
 * @param initiator_id ID of the initiator
 * @param invitee_id ID of the invitee
 * @param input_variables_ID Array of input variable IDs
 * @param input_variables_size Array of sizes corresponding to input variables
 * @param no_of_input_variables Number of input variables
 * @param output_variables_ID Array of output variable IDs
 * @param output_variables_size Array of sizes corresponding to output variables
 * @param no_of_output_variables Number of output variables
 */
void create_session(const char* base_url, int source_model_ID, int destination_model_ID, 
                      int initiator_id, int invitee_id,
                      int* input_variables_ID, int* input_variables_size, 
                      int no_of_input_variables, int* output_variables_ID, int* output_variables_size, 
                      int no_of_output_variables) {
    CURL *curl;
    CURLcode res;

    char full_url[MAX_URL_SIZE]; // Buffer to construct the full URL
    char postFields[4096]; // Buffer for JSON payload
    char arrays[1024]; // Buffer for temporary storage of array strings

    snprintf(full_url, sizeof(full_url), "%s/create_session", base_url);

    // Start constructing the JSON payload
    sprintf(postFields, "{\"source_model_ID\": \"%d\", \"destination_model_ID\": \"%d\", \"initiator_id\": \"%d\", \"invitee_id\": \"%d\", ",
            source_model_ID, destination_model_ID, initiator_id, invitee_id);

    // Append input variables ID and sizes to the JSON payload
    strcat(postFields, "\"input_variables_ID\": [");
    for (int i = 0; i < no_of_input_variables; ++i) {
        sprintf(arrays, "%s%d", (i > 0 ? ", " : ""), input_variables_ID[i]);
        strcat(postFields, arrays);
    }
    strcat(postFields, "], \"input_variables_size\": [");
    for (int i = 0; i < no_of_input_variables; ++i) {
        sprintf(arrays, "%s%d", (i > 0 ? ", " : ""), input_variables_size[i]);
        strcat(postFields, arrays);
    }

    // Append output variables ID and sizes to the JSON payload
    strcat(postFields, "], \"output_variables_ID\": [");
    for (int i = 0; i < no_of_output_variables; ++i) {
        sprintf(arrays, "%s%d", (i > 0 ? ", " : ""), output_variables_ID[i]);
        strcat(postFields, arrays);
    }
    strcat(postFields, "], \"output_variables_size\": [");
    for (int i = 0; i < no_of_output_variables; ++i) {
        sprintf(arrays, "%s%d", (i > 0 ? ", " : ""), output_variables_size[i]);
        strcat(postFields, arrays);
    }
    strcat(postFields, "]}");

    // Initialize and configure CURL
    curl_global_init(CURL_GLOBAL_ALL);
    curl = curl_easy_init();
    if(curl) {
        struct curl_slist *headers = NULL;
        headers = curl_slist_append(headers, "Content-Type: application/json");

        // Set CURL options for the POST request
        curl_easy_setopt(curl, CURLOPT_URL, full_url);
        curl_easy_setopt(curl, CURLOPT_HTTPHEADER, headers);
        curl_easy_setopt(curl, CURLOPT_POSTFIELDS, postFields);
        curl_easy_setopt(curl, CURLOPT_POSTFIELDSIZE, (long)strlen(postFields));

        // Perform the request and check for errors
        res = curl_easy_perform(curl);
        if(res != CURLE_OK)
            fprintf(stderr, "curl_easy_perform() failed: %s\n", curl_easy_strerror(res));

        // Cleanup CURL resources
        curl_easy_cleanup(curl);
        curl_slist_free_all(headers);
    }
    curl_global_cleanup();
}


/**
 * Function to join a session by making a POST request to the server with session ID and invitee ID.
 * This function constructs a JSON payload that includes the session ID and the invitee ID.
 * The invitee ID is used to authenticate the request and identify the user attempting to join the session.
 *
 * @param base_url Base URL of the server
 * @param session_id Array containing session identifiers
 * @param invitee_id Invitee identifier, used to authenticate the user and manage session access permissions.
 * @return int 1 if the operation was successful, 0 otherwise.
 */
int join_session(const char *base_url, const int session_id[], int invitee_id) {
    CURL *curl;
    CURLcode res;
    char postFields[1024];
    char full_url[MAX_URL_SIZE];
    char session_id_str[256];
    char invitee_id_str[32];

    // Construct the URL for the POST request
    snprintf(full_url, sizeof(full_url), "%s/join_session", base_url);
    // printf("Constructed URL: %s\n", full_url);  // Debugging print

    // Build the session_id string from the array
    strcpy(session_id_str, "");
    char temp[10];
    for (int i = 0; i < 5; ++i) {
        snprintf(temp, sizeof(temp), "%d", session_id[i]);
        strcat(session_id_str, temp);
        if (i < 4) strcat(session_id_str, ",");
    }

    // Format the invitee_id into a string
    snprintf(invitee_id_str, sizeof(invitee_id_str), "%d", invitee_id);

    // Construct the JSON payload
    snprintf(postFields, sizeof(postFields), "{\"session_id\": \"%s\", \"invitee_id\": %s}", session_id_str, invitee_id_str);
    // printf("Constructed Payload: %s\n", postFields);  // Debugging print

    // Initialize CURL
    curl_global_init(CURL_GLOBAL_ALL);
    curl = curl_easy_init();
    if (curl) {
        struct curl_slist *headers = NULL;
        headers = curl_slist_append(headers, "Content-Type: application/json");

        // Set the CURL options for the request
        curl_easy_setopt(curl, CURLOPT_URL, full_url);
        curl_easy_setopt(curl, CURLOPT_HTTPHEADER, headers);
        curl_easy_setopt(curl, CURLOPT_POSTFIELDS, postFields);

        // Perform the CURL request
        res = curl_easy_perform(curl);
        if (res == CURLE_OK) {
            curl_easy_cleanup(curl);
            curl_slist_free_all(headers);
            curl_global_cleanup();
            return 1;  // Success
        } else {
            fprintf(stderr, "curl_easy_perform() failed: %s\n", curl_easy_strerror(res));
        }

        // Cleanup CURL
        curl_easy_cleanup(curl);
        curl_slist_free_all(headers);
    }
    curl_global_cleanup();
    return 0;  // Failure
}

/**
 * Constructs a query string from an array of session IDs to be used in URL queries.
 * The function assumes the array always contains exactly 5 elements.
 * 
 * @param output Pointer to a string where the resulting query string will be stored.
 * @param session_id Array of integers representing session IDs.
 */
void format_session_id_query(char *output, const int session_id[]) {
    char buffer[50];  // Temporary buffer for formatting session IDs
    int i;

    strcpy(output, "session_id=");  // Initialize the output string with the query parameter name

    for (i = 0; i < 5; ++i) {  // Iterate over each session ID (always 5 IDs assumed)
        sprintf(buffer, "%d", session_id[i]);  // Convert the integer ID to a string
        strcat(output, buffer);  // Append the string ID to the output
        
        if (i < 4) {  // Check if it's not the last ID
            strcat(output, ",");  // Append a comma after the ID except for the last one
        }
    }
}

struct memory {
    char *response;
    size_t size;
};

static size_t get_session_status_callback(void *contents, size_t size, size_t nmemb, struct memory *mem) {
    size_t real_size = size * nmemb;
    char *ptr = realloc(mem->response, mem->size + real_size + 1);
    if (!ptr) {
        printf("Not enough memory\n");
        return 0;
    }
    mem->response = ptr;
    memcpy(&(mem->response[mem->size]), contents, real_size);
    mem->size += real_size;
    mem->response[mem->size] = '\0';  // Null-terminate the response
    return real_size;
}

int get_session_status(const char *base_url, const int session_id[]) {
    CURL *curl;
    CURLcode res;
    char url[256];
    struct memory chunk = {0};
    char session_id_str[256];

    // Build the session_id string from the array
    strcpy(session_id_str, "");
    char temp[10];
    for (int i = 0; i < 5; ++i) {
        snprintf(temp, sizeof(temp), "%d", session_id[i]);
        strcat(session_id_str, temp);
        if (i < 4) strcat(session_id_str, ",");
    }

    snprintf(url, sizeof(url), "%s/get_session_status?session_id=%s", base_url, session_id_str);

    chunk.response = malloc(1);
    chunk.size = 0;

    curl_global_init(CURL_GLOBAL_ALL);
    curl = curl_easy_init();
    if (curl) {
        curl_easy_setopt(curl, CURLOPT_URL, url);
        curl_easy_setopt(curl, CURLOPT_WRITEFUNCTION, get_session_status_callback);
        curl_easy_setopt(curl, CURLOPT_WRITEDATA, (void *)&chunk);

        res = curl_easy_perform(curl);
        if (res != CURLE_OK) {
            fprintf(stderr, "curl_easy_perform() failed: %s\n", curl_easy_strerror(res));
        } else {
            // Ensure the response is null-terminated
            chunk.response[chunk.size] = '\0';
            int status = atoi(chunk.response);  // Convert response to integer
            free(chunk.response);
            curl_easy_cleanup(curl);
            return status;
        }
        curl_easy_cleanup(curl);
    }
    curl_global_cleanup();
    free(chunk.response);
    return 0;  // Return 0 if there was an error
}


/**
 * Callback function to extract the "flag_status" value from a JSON response.
 * It searches for the "flag_status" key and converts the subsequent value to an integer.
 * 
 * @param contents Pointer to the data received from the server.
 * @param size Size of the data element.
 * @param nmemb Number of data elements.
 * @param userp Pointer to an integer where the flag status will be stored.
 * @return The number of bytes processed.
 */
static size_t get_variable_flag_callback(void *contents, size_t size, size_t nmemb, void *userp) {
    size_t real_size = size * nmemb;
    char* ptr = (char*) contents;
    char* found = strstr(ptr, "\"flag_status\":"); // Locate the "flag_status" key in the JSON response

    if (found) {
        found += 14; // Move past the key to the value
        *((int*)userp) = atoi(found); // Convert the value to an integer and store it
    } else {
        *((int*)userp) = -1; // Set to -1 if the key is not found or in case of an error
    }

    return real_size;
}

/**
 * Fetches the flag status of a variable from the server.
 * Constructs a URL query with session IDs and the variable ID, then makes a GET request.
 * 
 * @param base_url Base URL of the API server.
 * @param session_id Array containing session identifiers.
 * @param var_id Variable ID whose flag status is to be retrieved.
 * @return The flag status as an integer (-1 on error, otherwise the actual flag status).
 */
int get_variable_flag(const char* base_url, const int session_id[], int var_id) {
    CURL *curl;
    CURLcode res;
    char url[512];
    char session_query[256];  // Buffer for the session_id query part
    int flag_status = -1;  // Default to -1 to indicate an error

    // Generate session_id query from the array
    format_session_id_query(session_query, session_id);

    // Construct the full URL with the session ID and variable ID query parameters
    snprintf(url, sizeof(url), "%s/get_variable_flag?%s&var_id=%d", base_url, session_query, var_id);

    // Initialize CURL
    curl = curl_easy_init();
    if(curl) {
        // Set CURL options for the GET request
        curl_easy_setopt(curl, CURLOPT_URL, url);
        curl_easy_setopt(curl, CURLOPT_WRITEFUNCTION, get_variable_flag_callback);
        curl_easy_setopt(curl, CURLOPT_WRITEDATA, &flag_status);
        curl_easy_setopt(curl, CURLOPT_FAILONERROR, 1L);  // Set to fail on HTTP errors (status >= 400)

        // Perform the request and handle errors
        res = curl_easy_perform(curl);
        if(res != CURLE_OK) {
            fprintf(stderr, "curl_easy_perform() failed: %s\n", curl_easy_strerror(res));
        }

        // Clean up CURL resources
        curl_easy_cleanup(curl);
    }
    curl_global_cleanup();

    return flag_status;  // Return the flag status, -1 if there was an error, otherwise the actual flag status
}

/**
 * Callback function for processing data received from a CURL operation. It extracts the "size" of a variable from JSON.
 * @param ptr Pointer to the data received from the server.
 * @param size Size of one data element.
 * @param nmemb Number of data elements.
 * @param userdata Pointer to an integer where the size will be stored.
 * @return The total number of bytes processed.
 */
size_t get_variable_size_callback(char* ptr, size_t size, size_t nmemb, void* userdata) {
    size_t real_size = size * nmemb;  // Calculate total data size
    const char* key = "\"size\":";  // Define the key to search for
    char* found = strstr(ptr, key);  // Search for the "size" key in the response

    if (found) {
        found += strlen(key);  // Dynamically calculate the offset past the key to the value
        int extracted_size = atoi(found);  // Convert the string to an integer
        *(int*)userdata = extracted_size;  // Store the result in the provided userdata
    }
    return real_size;  // Return the number of bytes processed
}


/**
 * Fetches the size of a specific variable from the server using HTTP GET.
 * @param base_url Base URL of the server API.
 * @param session_id Array containing session identifiers.
 * @param var_id The variable ID whose size is to be fetched.
 * @return The size of the variable as an integer. Returns -1 if an error occurs or the size is not found.
 */
int get_variable_size(const char* base_url, const int session_id[], int var_id) {
    CURL *curl;
    CURLcode res;
    char full_url[MAX_URL_SIZE];
    char session_query[256];  // Buffer for session_id query part
    int size = -1;  // Default to -1 to indicate failure or not found

    // Generate the session_id query string from the array
    format_session_id_query(session_query, session_id);

    // Construct the URL with the session_id query and variable ID as parameters
    snprintf(full_url, sizeof(full_url), "%s/get_variable_size?%s&var_id=%d", base_url, session_query, var_id);

    // Initialize CURL
    curl = curl_easy_init();
    if (curl) {
        // Set CURL options for the GET request
        curl_easy_setopt(curl, CURLOPT_URL, full_url);
        curl_easy_setopt(curl, CURLOPT_WRITEFUNCTION, get_variable_size_callback);
        curl_easy_setopt(curl, CURLOPT_WRITEDATA, &size);

        // Execute the GET request and handle errors
        res = curl_easy_perform(curl);
        if (res != CURLE_OK) {
            fprintf(stderr, "curl_easy_perform() failed: %s\n", curl_easy_strerror(res));
        }

        // Clean up CURL resources
        curl_easy_cleanup(curl);
    }
    curl_global_cleanup();

    return size;  // Return the size of the variable, or -1 if there was an error
}

/**
 * Formats a series of session IDs into a header string suitable for HTTP headers.
 * Assumes that the session_id array always contains exactly 5 elements.
 * 
 * @param sessionHeader Pointer to a string where the resulting session ID header will be stored.
 * @param session_id Array of integers representing session IDs.
 */
void format_session_id_query_header(char *sessionHeader, const int session_id[]) {
    // Initialize the sessionHeader string with the header field name
    strcpy(sessionHeader, "Session-ID: ");

    // Iterate over the session IDs and format them into the sessionHeader string
    for (int i = 0; i < 5; ++i) {
        char temp[10]; // Smaller buffer suitable for individual session IDs

        // Format the current session ID as a string and store it in temp
        snprintf(temp, sizeof(temp), "%d", session_id[i]);

        // Append the formatted session ID to the sessionHeader
        strcat(sessionHeader, temp);

        // Add a comma separator between session IDs, unless it's the last one
        if (i < 4) {
            strcat(sessionHeader, ",");
        }
    }
}

/**
 * Sends data to the server using HTTP POST.
 * This function uses the CURL library to send an array of doubles as binary data to a specified server.
 *
 * @param base_url The base URL of the server API.
 * @param session_id Array containing session identifiers.
 * @param var_id The variable ID associated with the data being sent.
 * @param arr Pointer to the array of doubles to be sent.
 * @param n Number of elements in the array.
 * @return Returns 1 on success, 0 on failure, and -1 if CURL initialization fails.
 */
int send_data(const char* base_url, const int session_id[], int var_id, const double* arr, int n) {
    CURL *curl;
    CURLcode res;
    struct curl_slist *headers = NULL;
    char full_url[MAX_URL_SIZE];  // Buffer for full URL
    char sessionHeader[256];  // Buffer for formatted session ID header
    char varHeader[256];  // Buffer for variable ID header

    // Prepare the full URL for the data sending endpoint
    snprintf(full_url, sizeof(full_url), "%s/send_data", base_url);

    // Initialize CURL
    curl = curl_easy_init();
    if (!curl) {
        fprintf(stderr, "Failed to initialize curl\n");
        return -1;
    }

    // Format the session_id array into a string suitable for headers
    format_session_id_query_header(sessionHeader, session_id);
    snprintf(varHeader, sizeof(varHeader), "Var-ID: %d", var_id);

    // Prepare the headers
    headers = curl_slist_append(headers, "Content-Type: application/octet-stream");
    headers = curl_slist_append(headers, sessionHeader);
    headers = curl_slist_append(headers, varHeader);

    // Set CURL options for sending data
    curl_easy_setopt(curl, CURLOPT_URL, full_url);
    curl_easy_setopt(curl, CURLOPT_HTTPHEADER, headers);
    curl_easy_setopt(curl, CURLOPT_POSTFIELDS, arr);
    curl_easy_setopt(curl, CURLOPT_POSTFIELDSIZE, sizeof(double) * n);

    // Perform the HTTP POST request
    res = curl_easy_perform(curl);

    // Clean up headers and CURL handle
    curl_slist_free_all(headers);
    curl_easy_cleanup(curl);

    // Check if the request was successful
    if (res != CURLE_OK) {
        fprintf(stderr, "Failed to send data: %s\n", curl_easy_strerror(res));
        return 0;
    }

    return 1; // Return 1 on success, 0 on failure
}

/**
 * Structure to hold the data received from the server.
 */
struct MemoryStruct {
    char *memory;
    size_t size;
};

/**
 * Callback function to handle the data received from the server.
 * This function reallocates the buffer to accommodate the new data and appends it.
 * 
 * @param contents Pointer to the received data.
 * @param size Size of one data element.
 * @param nmemb Number of data elements.
 * @param userp User-provided pointer to MemoryStruct to store received data.
 * @return The total number of bytes processed, or 0 on memory allocation failure.
 */
static size_t receive_data_callback(void *contents, size_t size, size_t nmemb, void *userp) {
    size_t real_size = size * nmemb;
    struct MemoryStruct *mem = (struct MemoryStruct *)userp;

    char *ptr = realloc(mem->memory, mem->size + real_size + 1);
    if (ptr == NULL) {
        fprintf(stderr, "Not enough memory (realloc returned NULL)\n");
        return 0; // A return of 0 will stop the data transfer
    }

    mem->memory = ptr;
    memcpy(&(mem->memory[mem->size]), contents, real_size);
    mem->size += real_size;
    mem->memory[mem->size] = '\0'; // Null-terminate the buffer
    return real_size;
}

/**
 * Fetches data from the server, expecting a specific amount of binary data corresponding to an array of doubles.
 * 
 * @param base_url Base URL of the server.
 * @param session_id Array of session identifiers.
 * @param var_id Variable ID for which data is being fetched.
 * @param arr Pointer to an array of doubles where the fetched data will be stored.
 * @param n Number of doubles expected to be received.
 * @return 1 on successful reception and correct data size, 0 otherwise.
 */
int receive_data(const char* base_url, const int session_id[], int var_id, double* arr, int n) {
    CURL *curl;
    CURLcode res;
    struct MemoryStruct chunk;
    char full_url[512];
    char session_query[256];  // Buffer for session_id query part

    // Initialize the memory structure
    chunk.memory = malloc(1);  // Initially allocate 1 byte
    chunk.size = 0;            // No data at this point

    if (chunk.memory == NULL) {
        fprintf(stderr, "Memory allocation failed\n");
        return 0;
    }

    // Generate the session_id query from the array
    format_session_id_query(session_query, session_id);

    // Construct the URL with session ID and variable ID
    snprintf(full_url, sizeof(full_url), "%s/receive_data?%s&var_id=%d", base_url, session_query, var_id);

    curl = curl_easy_init();
    if (curl) {
        curl_easy_setopt(curl, CURLOPT_URL, full_url);
        curl_easy_setopt(curl, CURLOPT_WRITEFUNCTION, receive_data_callback);
        curl_easy_setopt(curl, CURLOPT_WRITEDATA, (void *)&chunk);
        curl_easy_setopt(curl, CURLOPT_USERAGENT, "libcurl-agent/1.0");

        // Perform the HTTP GET request
        res = curl_easy_perform(curl);
        if (res != CURLE_OK) {
            fprintf(stderr, "curl_easy_perform() failed: %s\n", curl_easy_strerror(res));
        } else {
            // Verify received data size matches the expected size
            if (chunk.size == n * sizeof(double)) {
                memcpy(arr, chunk.memory, chunk.size);
            } else {
                fprintf(stderr, "Received data size does not match expected size\n");
                res = CURLE_RECV_ERROR;
            }
        }

        // Clean up
        curl_easy_cleanup(curl);
        free(chunk.memory);
    } else {
        fprintf(stderr, "Failed to initialize curl\n");
        res = CURLE_FAILED_INIT;
    }

    return (res == CURLE_OK) ? 1 : 0; // Return 1 on success, 0 on failure
}


/**
 * Ends a session on the server by sending a POST request with the session ID and user ID as JSON.
 * This function constructs a JSON payload that includes the session ID and the user ID (which can be either an initiator_id or invitee_id).
 * The user_id is used to identify which user is attempting to end the session.
 * 
 * @param base_url The base URL of the server API.
 * @param session_id Array containing session identifiers.
 * @param user_id User identifier, used to authenticate the request and identify the user within the session context.
 */
void end_session(const char* base_url, const int session_id[], int user_id) {
    CURL *curl;
    CURLcode res;
    char full_url[MAX_URL_SIZE];
    char session_id_str[256];
    char postFields[1024];
    char user_id_str[32];

    snprintf(full_url, sizeof(full_url), "%s/end_session", base_url);

    strcpy(session_id_str, "");
    char temp[10];
    for (int i = 0; i < 5; ++i) {
        snprintf(temp, sizeof(temp), "%d", session_id[i]);
        strcat(session_id_str, temp);
        if (i < 4) strcat(session_id_str, ",");
    }

    snprintf(user_id_str, sizeof(user_id_str), "%d", user_id);
    snprintf(postFields, sizeof(postFields), "{\"session_id\": \"%s\", \"user_id\": %s}", session_id_str, user_id_str);

    curl_global_init(CURL_GLOBAL_ALL);
    curl = curl_easy_init();
    if (curl) {
        struct curl_slist *headers = NULL;
        headers = curl_slist_append(headers, "Content-Type: application/json");

        curl_easy_setopt(curl, CURLOPT_URL, full_url);
        curl_easy_setopt(curl, CURLOPT_HTTPHEADER, headers);
        curl_easy_setopt(curl, CURLOPT_POSTFIELDS, postFields);
        curl_easy_setopt(curl, CURLOPT_CUSTOMREQUEST, "POST");

        res = curl_easy_perform(curl);
        if (res != CURLE_OK) {
            fprintf(stderr, "curl_easy_perform() failed: %s\n", curl_easy_strerror(res));
        } else {
            printf("Session ended successfully.\n");
        }

        curl_easy_cleanup(curl);
        curl_slist_free_all(headers);
    }
    curl_global_cleanup();
}