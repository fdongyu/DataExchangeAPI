#include <curl/curl.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>


#define MAX_URL_SIZE 2048

/**
 * Structure to store session identifiers.
 */
typedef struct {
    int source_model_id;
    int destination_model_id;
    int initiator_id;
    int invitee_id;
    char instance_id[36];
} SessionID;

/**
 * Structure to hold the data received from the server.
 */
typedef struct  {
    char *data;
    size_t size;
} Memory;

/**
 * Construct a session ID string from the session ID struct. Allows a prefix to be added to the string.
 * 
 * @param buffer Buffer to store the session ID string
 * @param session_id Session ID struct containing the session ID
 * @param prefix Prefix to be added to the session ID string
 */

void build_session_id_string(char* buffer, const SessionID session_id, const char* prefix) {
    // Build the session_id string from the array
    // Calculate the size of the formatted string
    const int size = snprintf(NULL, 0, "%d%d%d%d", session_id.source_model_id, // int
                                                        session_id.destination_model_id, // int
                                                        session_id.initiator_id, // int
                                                        session_id.invitee_id); // int 
    if(strcmp(prefix, "\0") == 0)
        // No prefix - Just builds ID string
        snprintf(buffer, size+41, "%d,%d,%d,%d,%s", 
                                                        session_id.source_model_id, // int
                                                        session_id.destination_model_id, // int
                                                        session_id.initiator_id, // int
                                                        session_id.invitee_id, // int 
                                                        session_id.instance_id); // 36 chars
    else
        // Format the session ID array into a string suitable for headers
        snprintf(buffer, size + 41 + strlen(prefix), "%s%d,%d,%d,%d,%s", prefix,
                                                        session_id.source_model_id, // int
                                                        session_id.destination_model_id, // int
                                                        session_id.initiator_id, // int
                                                        session_id.invitee_id, // int 
                                                        session_id.instance_id); // 36 chars
    printf("Constructed Session ID: %s\n", buffer);  // Debugging print
}


/**
 * Construct a JSON payload for the session ID.
 * 
 * @param buffer Buffer to store the JSON payload
 * @param session_id Session ID struct containing the session ID
 * 
 * @return void
 */

void build_session_id_json(char* buffer, const SessionID session_id) {
    
    // Start constructing the JSON payload
    sprintf(buffer, "{\"source_model_id\": %d, \"destination_model_id\": %d, \"initiator_id\": %d, \"invitee_id\": %d, \"client_id\": \"%s\"}",
            session_id.source_model_id, session_id.destination_model_id, session_id.initiator_id, session_id.invitee_id, session_id.instance_id);
}

/**
 * Function to build a session ID from the received data.
 * 
 * @param chunk Memory struct containing the received data
 * @return SessionID Struct containing the session ID
 */
SessionID build_session_id(Memory* chunk) {
    SessionID session_id;
    char *start = strstr(chunk->data, "\"session_id\":{") + strlen("\"session_id\":{");
    char *token, *innerToken, *saveptr1, *saveptr2; 

    // Tokenize by comma first
    for (token = strtok_r(start, ",", &saveptr1); token != NULL; token = strtok_r(NULL, ",", &saveptr1)) {
        // Get the second token (value) directly
        strtok_r(token, ":", &saveptr2); // Skip the first token (key)
        innerToken = strtok_r(NULL, ":", &saveptr2); 

        if (strstr(token, "\"source_model_id\"")) {
            session_id.source_model_id = atoi(innerToken);
        } else if (strstr(token, "\"destination_model_id\"")) {
            session_id.destination_model_id = atoi(innerToken);
        } else if (strstr(token, "\"initiator_id\"")) {
            session_id.initiator_id = atoi(innerToken);
        } else if (strstr(token, "\"invitee_id\"")) {
            session_id.invitee_id = atoi(innerToken);
        } else if (strstr(token, "\"client_id\"")) {
            // Remove quotes
            innerToken = strtok_r(innerToken, "\"", &saveptr2); 
            strcpy(session_id.instance_id, innerToken);
        }
    }
    printf("Session ID: %d, %d, %d, %d, %s\n", session_id.source_model_id, session_id.destination_model_id, session_id.initiator_id, session_id.invitee_id, session_id.instance_id);  // Debugging print
    return session_id;
}

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
    Memory *mem = (Memory *)userp;

    char *ptr = realloc(mem->data, mem->size + real_size + 1);
    if (ptr == NULL) {
        fprintf(stderr, "Not enough memory (realloc returned NULL)\n");
        return 0; // A return of 0 will stop the data transfer
    }

    mem->data = ptr;
    memcpy(&(mem->data[mem->size]), contents, real_size);
    mem->size += real_size;
    mem->data[mem->size] = '\0'; // Null-terminate the buffer
    return real_size;
}


/**
 * Function to create a session on the server by making a POST request with JSON data.
 * @param base_url Base URL of the server
 * @param source_model_id ID of the source model
 * @param destination_model_id ID of the destination model
 * @param initiator_id ID of the initiator
 * @param invitee_id ID of the invitee
 * @param input_variables_id Array of input variable IDs
 * @param input_variables_size Array of sizes corresponding to input variables
 * @param no_of_input_variables Number of input variables
 * @param output_variables_id Array of output variable IDs
 * @param output_variables_size Array of sizes corresponding to output variables
 * @param no_of_output_variables Number of output variables
 */
void create_session(const char* base_url, int source_model_id, int destination_model_id, 
                      int initiator_id, int invitee_id,
                      int* input_variables_id, int* input_variables_size, 
                      int no_of_input_variables, int* output_variables_id, int* output_variables_size, 
                      int no_of_output_variables, SessionID* local_session_id) {
    CURL *curl;
    CURLcode res;

    char full_url[MAX_URL_SIZE]; // Buffer to construct the full URL
    char postFields[4096]; // Buffer for JSON payload
    char arrays[1024]; // Buffer for temporary storage of array strings
    char session_query[256];  // Buffer for session_id query part
    SessionID session_id;
    Memory chunk;

    chunk.data = (char*)malloc(1);
    chunk.size = 0;

    snprintf(full_url, sizeof(full_url), "%s/create_session", base_url);

    // Start constructing the JSON payload
    sprintf(postFields, "{\"source_model_id\": \"%d\", \"destination_model_id\": \"%d\", \"initiator_id\": \"%d\", \"invitee_id\": \"%d\", ",
            source_model_id, destination_model_id, initiator_id, invitee_id);

    // Append input variables ID and sizes to the JSON payload
    strcat(postFields, "\"input_variables_id\": [");
    for (int i = 0; i < no_of_input_variables; ++i) {
        sprintf(arrays, "%s%d", (i > 0 ? ", " : ""), input_variables_id[i]);
        strcat(postFields, arrays);
    }
    strcat(postFields, "], \"input_variables_size\": [");
    for (int i = 0; i < no_of_input_variables; ++i) {
        sprintf(arrays, "%s%d", (i > 0 ? ", " : ""), input_variables_size[i]);
        strcat(postFields, arrays);
    }

    // Append output variables ID and sizes to the JSON payload
    strcat(postFields, "], \"output_variables_id\": [");
    for (int i = 0; i < no_of_output_variables; ++i) {
        sprintf(arrays, "%s%d", (i > 0 ? ", " : ""), output_variables_id[i]);
        strcat(postFields, arrays);
    }
    strcat(postFields, "], \"output_variables_size\": [");
    for (int i = 0; i < no_of_output_variables; ++i) {
        sprintf(arrays, "%s%d", (i > 0 ? ", " : ""), output_variables_size[i]);
        strcat(postFields, arrays);
    }
    strcat(postFields, "]}");
    printf("Constructed Payload: %s\n", postFields);  // Debugging print

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
        curl_easy_setopt(curl, CURLOPT_WRITEFUNCTION, receive_data_callback);
        curl_easy_setopt(curl, CURLOPT_WRITEDATA, (void *)&chunk);
        curl_easy_setopt(curl, CURLOPT_USERAGENT, "libcurl-agent/1.0");
        

        // Perform the request and check for errors
        res = curl_easy_perform(curl);
        if(res != CURLE_OK)
            fprintf(stderr, "curl_easy_perform() failed: %s\n", curl_easy_strerror(res));

        // Cleanup CURL resources
        curl_easy_cleanup(curl);
        curl_slist_free_all(headers);

        // Extract the session ID from the received data
        *local_session_id = build_session_id(&chunk);

        free(chunk.data);
        printf("(C) Session ID return: %d, %d, %d, %d, %s\n", local_session_id->source_model_id, local_session_id->destination_model_id, local_session_id->initiator_id, local_session_id->invitee_id, local_session_id->instance_id);  // Debugging print

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
int join_session(const char *base_url, const SessionID* session_id, int invitee_id) {
    CURL *curl;
    CURLcode res;
    char postFields[1024];
    char full_url[MAX_URL_SIZE];
    char session_id_str[256];
    char invitee_id_str[32];

    // Construct the URL for the POST request
    snprintf(full_url, sizeof(full_url), "%s/join_session", base_url);
    // printf("Constructed URL: %s\n", full_url);  // Debugging print

    // // Build the session_id string from the array
    // strcpy(session_id_str, "");
    // char temp[10];
    // for (int i = 0; i < 5; ++i) {
    //     snprintf(temp, sizeof(temp), "%d", session_id[i]);
    //     strcat(session_id_str, temp);
    //     if (i < 4) strcat(session_id_str, ",");
    // }
    build_session_id_json(session_id_str, *session_id);

    // Construct the JSON payload
    snprintf(postFields, sizeof(postFields), "{\"session_id\": %s, \"invitee_id\": %d}", session_id_str, invitee_id);
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


static size_t get_session_status_callback(void *contents, size_t size, size_t nmemb, Memory *mem) {
    size_t real_size = size * nmemb;
    char *ptr = realloc(mem->data, mem->size + real_size + 1);
    if (!ptr) {
        printf("Not enough memory\n");
        return 0;
    }
    mem->data = ptr;
    memcpy(&(mem->data[mem->size]), contents, real_size);
    mem->size += real_size;
    mem->data[mem->size] = '\0';  // Null-terminate the response
    return real_size;
}

int get_session_status(const char *base_url, const SessionID* session_id) {
    CURL *curl;
    CURLcode res;
    char url[256];
    Memory chunk = {0};
    char session_id_str[256];

    // Build the session_id string from the array
    // strcpy(session_id_str, "");
    // char temp[10];
    // for (int i = 0; i < 5; ++i) {
    //     snprintf(temp, sizeof(temp), "%d", session_id[i]);
    //     strcat(session_id_str, temp);
    //     if (i < 4) strcat(session_id_str, ",");
    // }
    build_session_id_string(session_id_str, *session_id, "");

    snprintf(url, sizeof(url), "%s/get_session_status?session_id=%s", base_url, session_id_str);

    chunk.data = malloc(1);
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
            chunk.data[chunk.size] = '\0';
            int status = atoi(chunk.data);  // Convert response to integer
            free(chunk.data);
            curl_easy_cleanup(curl);
            return status;
        }
        curl_easy_cleanup(curl);
    }
    curl_global_cleanup();
    free(chunk.data);
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
int get_variable_flag(const char* base_url, const SessionID* session_id, int var_id) {
    CURL *curl;
    CURLcode res;
    char url[512];
    char session_query[256];  // Buffer for the session_id query part
    int flag_status = -1;  // Default to -1 to indicate an error

    // Generate session_id query from the array
    build_session_id_string(session_query, *session_id, "session_id=");

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
int get_variable_size(const char* base_url, const SessionID* session_id, int var_id) {
    CURL *curl;
    CURLcode res;
    char full_url[MAX_URL_SIZE];
    char session_query[256];  // Buffer for session_id query part
    int size = -1;  // Default to -1 to indicate failure or not found

    // Generate the session_id query string from the array
    build_session_id_string(session_query, *session_id, "session_id=");

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
int send_data(const char* base_url, const SessionID* session_id, int var_id, const double* arr, int n) {
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
    build_session_id_string(sessionHeader, *session_id, "Session-ID: ");
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
 * Fetches data from the server, expecting a specific amount of binary data corresponding to an array of doubles.
 * 
 * @param base_url Base URL of the server.
 * @param session_id Array of session identifiers.
 * @param var_id Variable ID for which data is being fetched.
 * @param arr Pointer to an array of doubles where the fetched data will be stored.
 * @param n Number of doubles expected to be received.
 * @return 1 on successful reception and correct data size, 0 otherwise.
 */
int receive_data(const char* base_url, const SessionID* session_id, int var_id, double* arr, int n) {
    CURL *curl;
    CURLcode res;
    Memory chunk;
    char full_url[MAX_URL_SIZE];
    char session_query[256];  // Buffer for session_id query part
    char postFields[1024];  // Buffer for JSON payload

    // Initialize the memory structure
    chunk.data = malloc(1);  // Initially allocate 1 byte
    chunk.size = 0;            // No data at this point

    if (chunk.data == NULL) {
        fprintf(stderr, "Memory allocation failed\n");
        return 0;
    }

    // Generate the session_id query from the array
    build_session_id_json(session_query, *session_id);

    // Construct the JSON payload
    snprintf(postFields, sizeof(postFields), "{\"session_id\": %s, \"param_id\": %d}", session_query, var_id);

    // Construct the full URL
    snprintf(full_url, sizeof(full_url), "%s/receive_data", base_url);

    curl = curl_easy_init();
    if (curl) {
        struct curl_slist *headers = NULL;
        headers = curl_slist_append(headers, "Content-Type: application/json");

        curl_easy_setopt(curl, CURLOPT_URL, full_url);
        curl_easy_setopt(curl, CURLOPT_WRITEFUNCTION, receive_data_callback);
        curl_easy_setopt(curl, CURLOPT_WRITEDATA, (void *)&chunk);
        curl_easy_setopt(curl, CURLOPT_HTTPHEADER, headers);
        curl_easy_setopt(curl, CURLOPT_POSTFIELDS, postFields);
        curl_easy_setopt(curl, CURLOPT_USERAGENT, "libcurl-agent/1.0");

        // Perform the HTTP GET request
        res = curl_easy_perform(curl);
        if (res != CURLE_OK) {
            fprintf(stderr, "curl_easy_perform() failed: %s\n", curl_easy_strerror(res));
        } else {
            // Verify received data size matches the expected size
            if (chunk.size == n * sizeof(double)) {
                memcpy(arr, chunk.data, chunk.size);
            } else {
                fprintf(stderr, "Received data size does not match expected size\n");
                res = CURLE_RECV_ERROR;
            }
        }

        // Clean up
        curl_easy_cleanup(curl);
        free(chunk.data);
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
void end_session(const char* base_url, const SessionID* session_id, char* user_id) {
    CURL *curl;
    CURLcode res;
    char full_url[MAX_URL_SIZE];
    char session_id_str[256];
    char postFields[1024];
    // char user_id_str[32];
    Memory chunk;

    chunk.data = malloc(1);
    chunk.size = 0;


    // strcpy(session_id_str, "");
    // char temp[10];
    // for (int i = 0; i < 5; ++i) {
    //     snprintf(temp, sizeof(temp), "%d", session_id[i]);
    //     strcat(session_id_str, temp);
    //     if (i < 4) strcat(session_id_str, ",");
    // }
    build_session_id_json(postFields, *session_id);


    // snprintf(user_id_str, sizeof(user_id_str), "%s", user_id);
    // snprintf(postFields, sizeof(postFields), "{\"session_id\": \"%s\", \"user_id\": %s}", session_id_str, user_id_str);
    // snprintf(postFields, sizeof(postFields), "", session_id_str);
    printf("Constructed Payload: %s\n", postFields);  // Debugging print
    snprintf(full_url, sizeof(full_url), "%s/end_session", base_url);


    curl_global_init(CURL_GLOBAL_ALL);
    curl = curl_easy_init();
    if (curl) {
        struct curl_slist *headers = NULL;
        headers = curl_slist_append(headers, "Content-Type: application/json");

        curl_easy_setopt(curl, CURLOPT_URL, full_url);
        // curl_easy_setopt(curl, CURLOPT_WRITEFUNCTION, build_session_id);
        // curl_easy_setopt(curl, CURLOPT_WRITEDATA, (void *)&chunk);
        curl_easy_setopt(curl, CURLOPT_HTTPHEADER, headers);
        curl_easy_setopt(curl, CURLOPT_POSTFIELDS, postFields);
        curl_easy_setopt(curl, CURLOPT_USERAGENT, "libcurl-agent/1.0");

        res = curl_easy_perform(curl);
        if (res != CURLE_OK) {
            fprintf(stderr, "curl_easy_perform() failed: %s\n", curl_easy_strerror(res));
        } else {
            printf("Session ended successfully.\n");
        }

        curl_easy_cleanup(curl);
    }
    curl_global_cleanup();
}