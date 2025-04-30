<template>
  <div>
    <!-- Global Error Alert -->
    <v-alert
      v-if="chatError"
      :type="chatErrorMessage.includes('Database') ? 'warning' : 'error'"
      :color="chatErrorMessage.includes('Database') ? 'amber darken-2' : 'error'"
      dense
      dismissible
      class="mb-3"
      transition="scale-transition"
    >
      <v-icon left>{{ chatErrorMessage.includes('Database') 
        ? 'mdi-database-off' : 'mdi-alert-circle' }}</v-icon>
      <strong>{{ chatErrorMessage.includes('Database') 
        ? 'Database Error:' : 'Chat System Error:' }}</strong> {{ chatErrorMessage }}
    </v-alert>

    <!-- Main Card with Votes -->
    <v-card>
      <v-card-title>
        <v-btn 
          v-if="isAdmin"
          class="text-capitalize" 
          color="primary" 
          @click.stop="openCreateVoteDialog()"
        >
          Create Vote
        </v-btn>
        <v-tooltip v-else bottom>
          <template #activator="{ on, attrs }">
            <v-btn 
              class="text-capitalize" 
              color="primary" 
              disabled
              v-bind="attrs"
              v-on="on"
            >
              Create Vote
            </v-btn>
          </template>
          <span>Only administrators can create votes</span>
        </v-tooltip>
        <v-alert
          v-if="!isAdmin"
          type="error"
          dense
          class="mt-2"
        >
          You do not have permission to create votes. Please contact an administrator.
        </v-alert>
      </v-card-title>

      <!-- List of Votes -->
      <v-expansion-panels v-if="hasVotes">
        <v-expansion-panel 
          v-for="vote in votes" 
          :key="vote.id"
        >
          <v-expansion-panel-header>
            <div class="d-flex align-center">
              <span class="font-weight-bold">{{ vote.title }}</span>
              <v-spacer></v-spacer>
              <v-btn 
                color="success"
                small
                class="mr-2"
                @click.stop="openVoteDialog(vote)"
              >
                <v-icon left small>mdi-check-circle</v-icon>
                Vote
              </v-btn>
            </div>
          </v-expansion-panel-header>
          <v-expansion-panel-content>
            <div class="mb-2">
              <em>{{ vote.description }}</em>
            </div>
            <div>
              <v-btn
                v-for="(option, index) in vote.options"
                :key="index"
                class="mr-2"
                color="primary"
                @click="submitVote(vote.id, option)"
              >
                {{ option }}
              </v-btn>
            </div>
            <div class="mt-2">
              <strong>Results:</strong>
              <div v-for="(count, option) in vote.results" :key="option">
                {{ option }}: {{ count }} votes
              </div>
            </div>
          </v-expansion-panel-content>
        </v-expansion-panel>
      </v-expansion-panels>

      <!-- Chat Box -->
      <v-card class="mt-4">
        <v-card-title>
          Chat
        </v-card-title>
        <v-card-text>
          <div>
            <!-- Messages -->
            <div v-for="(message, index) in messages" :key="index" class="mb-2">
<strong :style="{ color: 
getUserColor(message.user) }">{{ message.user }}:</strong> {{ message.text }}
            </div>
            <v-textarea
              v-model="newMessage"
              label="Type your message"
              rows="2"
              outlined
            />
            <v-btn 
              class="mt-2" 
              color="primary" 
              @click="sendMessage"
            >Send</v-btn>
          </div>
        </v-card-text>
      </v-card>

      <!-- Dialog for Creating a Vote -->
      <v-dialog v-model="dialogCreateVote" max-width="500px">
        <v-card>
          <v-card-title class="headline">Create Vote</v-card-title>
          <v-card-text>
            <v-text-field
              v-model="newVote.title"
              label="Vote Title"
              :error="showErrors && !newVote.title"
              :error-messages="showErrors && !newVote.title ? ['* Required field'] : []"
              required
            />
            <v-textarea
              v-model="newVote.description"
              label="Description"
              rows="3"
            />
            <v-text-field
              v-model="newVote.options"
              label="Options (comma-separated)"
              @input="newVote.options = $event.split(',').map(o => o.trim())"
            />
          </v-card-text>
          <v-card-actions>
            <v-spacer />
            <v-btn text @click="closeVoteDialog">Cancel</v-btn>
            <v-btn color="primary" text @click="saveVote">Save</v-btn>
          </v-card-actions>
        </v-card>
      </v-dialog>
    </v-card>
  </div>
</template>

<script>
export default {
  layout: 'project',
  middleware: ['check-auth', 'auth', 'setCurrentProject'],

  data() {
    return {
      dialogCreateVote: false,
      showErrors: false,
      votes: [
        {
          id: 1,
          title: 'Vote 1',
          description: 'Description for Vote 1',
          options: ['Option A', 'Option B', 'Option C'],
          results: { 'Option A': 0, 'Option B': 0, 'Option C': 0 }
        },
        {
          id: 2,
          title: 'Vote 2',
          description: 'Description for Vote 2',
          options: ['Option X', 'Option Y'],
          results: { 'Option X': 0, 'Option Y': 0 }
        }
      ],
      newVote: {
        title: '',
        description: '',
        options: []
      },
      currentDocument: null,
      messages: [],
      newMessage: '',
      documents: [], // Will contain available documents
      selectedDocumentId: null,
      chatError: false,
      chatErrorMessage: '',
      socket: null,
      socketConnected: false,
      socketError: false,
      messagePollingInterval: null,
    };
  },

  computed: {
    projectId() {
      return this.$route.params.id;
    },
    hasVotes() {
      return this.votes && this.votes.length > 0;
    },
    isAdmin() {
      return true; // Replace with actual admin check logic
    }
  },

  created() {
    // Get document info from route query parameters if available
    if (this.$route.query.documentId) {
      const document = {
        id: this.$route.query.documentId,
        title: this.$route.query.documentTitle || `Document #${this.$route.query.documentId}`
      };
      
      // Set this as the current document
      this.currentDocument = document;
      console.log('Document loaded from route:', document);
    }
    
    this.fetchVotes();
    this.connectWebSocket();
  },

  beforeDestroy() {
    // Close WebSocket connection when component is destroyed
    if (this.socket) {
      this.socket.close();
    }
    // Clear polling interval if set
    if (this.messagePollingInterval) {
      clearInterval(this.messagePollingInterval);
    }
  },

  methods: {
    openCreateVoteDialog() {
      this.dialogCreateVote = true;
    },
    closeVoteDialog() {
      this.dialogCreateVote = false;
      this.showErrors = false;
      this.newVote = {
        title: '',
        description: '',
        options: []
      };
    },
    saveVote() {
      this.showErrors = true;
      if (!this.newVote.title || this.newVote.options.length === 0) {
        return;
      }

      try {
        // Create the vote first
        const newVote = {
          ...this.newVote,
          id: Date.now(),
          results: this.newVote.options.reduce((acc, option) => {
            acc[option] = 0;
            return acc;
          }, {})
        };
        
        // If we have a current document, link this vote to it
        if (this.currentDocument) {
          newVote.documentId = this.currentDocument.id;
          newVote.documentTitle = this.currentDocument.title;
        }

        this.votes.push(newVote);
        this.closeVoteDialog();
      } catch (error) {
        console.error('Error saving vote:', error);
      }
    },
    openVoteDialog(vote) {
      console.log('Vote dialog opened for:', vote);
      
      // Set this vote's document as the current document
      // This assumes each vote has a documentId property
      // If it doesn't, you'll need to add it when creating votes
      if (vote.documentId) {
        // Find the document that this vote belongs to
        const document = {
          id: vote.documentId,
          title: vote.documentTitle || `Document for ${vote.title}`
        };
        
        // Select this document to load its specific messages
        this.selectDocument(document);
      } else {
        // If no document ID is associated with this vote yet,
        // Create a temporary document object for this vote
        const document = {
          id: `vote_${vote.id}`, // Use the vote ID as a document ID
          title: vote.title // Use vote title as document title
        };
        
        // Select this document to load its specific messages
        this.selectDocument(document);
      }
    },
    linkVoteToDocument(voteId, documentId, documentTitle) {
      const vote = this.votes.find(v => v.id === voteId);
      if (vote) {
        vote.documentId = documentId;
        vote.documentTitle = documentTitle;
      }
    },
    fetchVotes() {
      try {
        this.votes = [
          { id: 1, title: 'Vote 1', description: 'Description for Vote 1', options: ['Option A', 'Option B', 'Option C'], results: { 'Option A': 0, 'Option B': 0, 'Option C': 0 } },
          { id: 2, title: 'Vote 2', description: 'Description for Vote 2', options: ['Option X', 'Option Y'], results: { 'Option X': 0, 'Option Y': 0 } }
        ];
      } catch (error) {
        console.error('Error fetching votes:', error);
      }
    },
    async fetchMessages() {
      try {
        const projectId = this.projectId;
        console.log(`Fetching messages for project ${projectId}`);
        
        // Remove trailing slash and check if we need to adjust the base path
        const response = await this.$axios.get(`/v1/projects/${projectId}/chat`);
        this.messages = response.data;
        console.log(`Loaded ${this.messages.length} messages for project ${projectId}`);
      } catch (error) {
        console.error('Error fetching messages:', error);
        this.messages = [];
        this.chatError = true;
        this.chatErrorMessage = 'Failed to load messages. Please try again later.';
      }
    },
    connectWebSocket() {
      const projectId = this.projectId;
      
      // Close any existing connection
      if (this.socket) {
        this.socket.close();
      }
      
      try {
        // Point directly to Django server (adjust port if needed)
        const backendHost = 'localhost:8000'; // Change this to where your Django server runs
        const protocol = window.location.protocol === 'https:' ? 'wss://' : 'ws://';
        const wsUrl = `${protocol}${backendHost}/ws/projects/${projectId}/chat/`;
        
        console.log(`Attempting to connect WebSocket to: ${wsUrl}`);
        this.socket = new WebSocket(wsUrl);
        
        this.socket.onopen = () => {
          console.log(`WebSocket connected for project ${projectId}`);
          this.socketConnected = true;
          this.socketError = false;
          
          // Clear any previous error since we're now connected
          this.chatError = false;
        };
        
        this.socket.onmessage = (event) => {
          const data = JSON.parse(event.data);
          console.log('WebSocket message received:', data);
          
          // Add message to the list if it's not already there
          const messageExists = this.messages.some(m => 
            m.user === data.user && m.text === data.text
          );
          
          if (!messageExists) {
            this.messages.push(data);
          }
        };
        
        this.socket.onclose = (event) => {
          console.log('WebSocket closed, reconnecting in 5s...', event.code);
          this.socketConnected = false;
          
          // Try to reconnect after a delay
          setTimeout(() => {
            this.connectWebSocket();
          }, 5000);
        };
        
        this.socket.onerror = (error) => {
          console.error('WebSocket error:', error);
          this.socketConnected = false;
          this.socketError = true;
          
          // Set up error message
          this.chatError = true;
          this.chatErrorMessage = "WebSocket connection failed. Using standard HTTP for messages.";
          
          // Start polling for messages since WebSocket failed
          this.startMessagePolling();
        };
      } catch (error) {
        console.error('Error creating WebSocket:', error);
        this.socketConnected = false;
        this.socketError = true;
        this.chatError = true;
        this.chatErrorMessage = "WebSocket initialization failed. Using standard HTTP for messages.";
        
        // Start polling for messages since WebSocket failed
        this.startMessagePolling();
      }
    },
    startMessagePolling() {
      console.log('Starting message polling as fallback');
      // Clear existing polling interval if any
      if (this.messagePollingInterval) {
        clearInterval(this.messagePollingInterval);
      }
      
      // Fetch messages immediately
      this.fetchMessages();
      
      // Set up polling interval
      this.messagePollingInterval = setInterval(() => {
        this.fetchMessages();
      }, 3000); // Poll every 3 seconds
    },
    sendMessage() {
      if (this.newMessage.trim()) {
        try {
          const currentUsername = this.$store.state.auth.username || 'Anonymous';
          const message = this.newMessage.trim();
          
          // Clear the input field immediately for better UX
          this.newMessage = '';
          
          if (this.socketConnected) {
            // Try to send via WebSocket first
            try {
              console.log('Attempting to send message via WebSocket');
              this.socket.send(JSON.stringify({
                user: currentUsername,
                message
              }));
              console.log('WebSocket message sent successfully');
            } catch (wsError) {
              // WebSocket failed, fall back to HTTP
              console.error('WebSocket send failed, falling back to HTTP:', wsError);
              this.sendMessageViaHttp(currentUsername, message);
            }
          } else {
            // WebSocket not connected, use HTTP directly
            console.log('WebSocket not connected, using HTTP API');
            this.sendMessageViaHttp(currentUsername, message);
          }
        } catch (error) {
          console.error('Error sending message:', error);
          this.chatError = true;
          this.chatErrorMessage = "Failed to send message: " + error.message;
          
          // Hide error after 5 seconds
          setTimeout(() => {
            this.chatError = false;
          }, 5000);
        }
      }
    },

    async sendMessageViaHttp(username, message) {
      try {
        const projectId = this.projectId;
        
        // Send message via HTTP API
        await this.$axios.post(`/v1/projects/${projectId}/chat`, {
          user: username,
          message
        });
        
        console.log('HTTP message sent successfully');
        
        // Refresh messages to show the newly added one
        await this.fetchMessages();
      } catch (error) {
        console.error('HTTP fallback error:', error);
        this.chatError = true;
        
        // Check if this might be a database connection error
        if (error.response && (error.response.status === 500 || error.response.status === 503)) {
          this.chatErrorMessage = "Database connection error. Messages cannot be sent or received. Please try again later.";
        } else {
          this.chatErrorMessage = "Failed to send message to server. Please check your connection.";
        }
        
        // Hide error after 8 seconds (longer for database error)
        setTimeout(() => {
          this.chatError = false;
        }, 8000);
      }
    },
    selectDocument(document) {
      this.currentDocument = document;
      // Reconnect WebSocket when document changes
      this.connectWebSocket();
    },
    getUserColor(username) {
      // Define a palette of highly distinct colors
      const colors = [
        '#FF0000', // Red
        '#00A0FF', // Blue
        '#00FF00', // Green
        '#FF00FF', // Magenta
        '#FFA500', // Orange
        '#9400D3', // Purple
        '#008080', // Teal
        '#FF4500', // Orange-Red
        '#FFD700', // Gold
        '#4B0082', // Indigo
        '#800000', // Maroon
        '#00FFFF', // Cyan
        '#8B4513', // Brown
        '#000000', // Black
        '#708090'  // Slate Gray
      ];
      
      // Create a more distributed hash from the username
      let hash = 0;
      for (let i = 0; i < username.length; i++) {
        // Use a prime number (31) to improve distribution
        hash = ((hash << 5) - hash) + username.charCodeAt(i);
        hash = hash & hash; // Convert to 32bit integer
      }
      
      // Use the hash to pick a color from our palette
      const index = Math.abs(hash) % colors.length;
      return colors[index];
    }
  }
};
</script>