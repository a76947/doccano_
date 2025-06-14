<template>
  <div>
    <!-- Global Error Alert -->
    <v-alert
      v-if="error"
      type="error"
      dense
      dismissible
      class="mb-3"
      transition="scale-transition"
    >
      <v-icon left>mdi-alert-circle</v-icon>
      <strong>{{ errorMessage }}</strong>
    </v-alert>

    <!-- Dialog for Creating a Session -->
    <v-dialog v-model="dialogCreateSession" max-width="500px" persistent>
      <v-card>
        <v-card-title class="headline">Create Voting Session</v-card-title>
        <v-card-text>
          <v-text-field
            v-model="newSession.title"
            label="Session Title"
            :error="showErrors && !newSession.title"
            :error-messages="showErrors && !newSession.title ? ['* Required field'] : []"
            required
          />
          <v-textarea
            v-model="newSession.description"
            label="Description"
            rows="3"
          />
        </v-card-text>
        <v-card-actions>
          <v-spacer />
          <v-btn text @click="closeSessionDialog">Cancel</v-btn>
          <v-btn color="primary" text @click="saveSession">Save</v-btn>
        </v-card-actions>
      </v-card>
    </v-dialog>

    <!-- No Sessions View -->
    <v-card v-if="!selectedSession">
      <v-card-title>
        Voting Sessions
        <v-spacer></v-spacer>
        <v-btn 
          v-if="isAdmin"
          class="text-capitalize" 
          color="primary" 
          @click="openCreateSessionDialog"
        >
          Create Session
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
              Create Session
            </v-btn>
          </template>
          <span>Only administrators can create sessions</span>
        </v-tooltip>
      </v-card-title>
      
      <v-card-text>
        <v-alert
          v-if="!isAdmin && sessions.length === 0"
          type="info"
          dense
        >
          There are no active voting sessions. Please wait for an administrator to create one.
        </v-alert>

        <!-- List of Sessions -->
        <v-list v-if="sessions.length > 0" two-line>
          <v-list-item
            v-for="session in sessions"
            :key="session.id"
            @click="selectSession(session)"
          >
            <v-list-item-content>
              <v-list-item-title>
                {{ session.title }}
                <span v-if="session.ended" class="ml-2 caption red--text">(ENDED)</span>
              </v-list-item-title>
              <v-list-item-subtitle>
                Created by {{ session.created_by }} on {{ formatDate(session.created_at) }}
              </v-list-item-subtitle>
            </v-list-item-content>
            <v-list-item-action>
              <v-btn icon>
                <v-icon>mdi-chevron-right</v-icon>
              </v-btn>
            </v-list-item-action>
          </v-list-item>
        </v-list>
      </v-card-text>
    </v-card>

    <!-- Session View -->
    <div v-else>
      <!-- Session Header -->
      <v-card class="mb-4">
        <v-card-title>
          <v-btn icon class="mr-2" @click="backToSessions">
            <v-icon>mdi-arrow-left</v-icon>
          </v-btn>
          {{ selectedSession.title }}
          <v-spacer></v-spacer>
          <v-btn 
            v-if="isAdmin && !selectedSession.ended"
            text
            color="warning"
            class="mr-2"
            @click="confirmEndSession"
          >
            <v-icon left>mdi-clock-end</v-icon>
            End Session
          </v-btn>
          <v-btn 
            v-if="isAdmin"
            text
            color="error"
            @click="confirmDeleteSession"
          >
            <v-icon left>mdi-delete</v-icon>
            Delete Session
          </v-btn>
        </v-card-title>
        <v-card-text>
          <div>{{ selectedSession.description }}</div>
          <div class="caption grey--text">
      Created by {{ selectedSession.created_by }} on {{ formatDate(selectedSession.created_at) }}
            <span v-if="selectedSession.ended" class="ml-2 red--text">
              (ENDED)
            </span>
          </div>
        </v-card-text>
      </v-card>

      <!-- Main Card with Votes -->
      <v-card class="mb-4">
        <v-card-title>
          Votes
          <v-spacer></v-spacer>
          <v-btn 
            v-if="isAdmin && !selectedSession.ended"
            class="text-capitalize" 
            color="primary" 
            @click.stop="openCreateVoteDialog()"
          >
            Create Vote
          </v-btn>
        </v-card-title>

        <!-- No votes message -->
        <v-card-text v-if="!hasVotes">
          <v-alert
            type="info"
            dense
          >
            There are no votes in this session yet.
            <span v-if="isAdmin"> Click 'Create Vote' to add one.</span>
          </v-alert>
        </v-card-text>

        <!-- List of Votes -->
        <v-expansion-panels v-if="hasVotes">
          <v-expansion-panel 
            v-for="vote in sessionVotes" 
            :key="vote.id"
          >
            <v-expansion-panel-header>
              <div class="d-flex align-center">
                <span class="font-weight-bold">{{ vote.title }}</span>
                <v-spacer></v-spacer>
              </div>
            </v-expansion-panel-header>
            <v-expansion-panel-content>
              <div class="mb-2">
                <em>{{ vote.description }}</em>
              </div>
              <div>
                <v-btn
                  v-for="option in vote.options"
                  :key="option"
                  class="mr-2 mb-2"
                  color="primary"
                  :disabled="selectedSession.ended"
                  @click="submitVote(vote.id, option)"
                >
                  {{ option }}
                </v-btn>
              </div>
              <div class="mt-4">
                <strong>Results:</strong>
                <v-list dense>
                  <v-list-item v-for="option in vote.options" :key="option">
                    <v-list-item-content>
<v-list-item-title>{{ option }}: {{ vote.results[option] || 0 }} votes</v-list-item-title>
                    </v-list-item-content>
                  </v-list-item>
                </v-list>
              </div>
            </v-expansion-panel-content>
          </v-expansion-panel>
        </v-expansion-panels>
      </v-card>

      <!-- Chat Box -->
      <v-card>
        <v-card-title>
          Chat
        </v-card-title>
        <v-card-text>
<div ref="chatContainer" class="chat-messages mb-2" style="max-height: 300px; overflow-y: auto;">
            <div v-if="sessionMessages.length === 0" class="text-center pa-4 grey--text">
              No messages yet. Start the conversation!
            </div>
            <!-- Messages -->
            <div v-for="message in sessionMessages" :key="message.id" class="mb-2">
<strong :style="{ color: getUserColor(message.user) }">{{ message.user }}:
</strong> {{ message.text }}
              <div class="caption grey--text">{{ formatTime(message.timestamp) }}</div>
            </div>
          </div>
          <v-textarea
            v-model="newMessage"
            label="Type your message"
            rows="2"
            outlined
            :disabled="selectedSession.ended"
            @keyup.enter="sendMessage"
          />
          <v-btn 
            class="mt-2" 
            color="primary"
            :disabled="selectedSession.ended" 
            @click="sendMessage"
          >Send</v-btn>
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
            <v-combobox
              v-model="newVote.options"
              label="Options"
              multiple
              chips
              :error="showErrors && (!newVote.options || newVote.options.length === 0)"
              :error-messages="showErrors && (!newVote.options ||
              newVote.options.length === 0) ? ['* At least one option required'] : []"
            />
          </v-card-text>
          <v-card-actions>
            <v-spacer />
            <v-btn text @click="closeVoteDialog">Cancel</v-btn>
            <v-btn color="primary" text @click="saveVote">Save</v-btn>
          </v-card-actions>
        </v-card>
      </v-dialog>

      <!-- Confirmation Dialog -->
      <v-dialog v-model="dialogConfirm" max-width="400px">
        <v-card>
          <v-card-title>Confirm Deletion</v-card-title>
          <v-card-text>
            Are you sure you want to delete this session? This action cannot be undone.
          </v-card-text>
          <v-card-actions>
            <v-spacer />
            <v-btn text @click="dialogConfirm = false">Cancel</v-btn>
            <v-btn color="error" text @click="deleteSession">Delete</v-btn>
          </v-card-actions>
        </v-card>
      </v-dialog>

      <!-- End Session Confirmation Dialog -->
      <v-dialog v-model="dialogEndSession" max-width="400px">
        <v-card>
          <v-card-title>End Session</v-card-title>
          <v-card-text>
            Are you sure you want to end this session? Users will no longer be able to vote or chat.
          </v-card-text>
          <v-card-actions>
            <v-spacer />
            <v-btn text @click="dialogEndSession = false">Cancel</v-btn>
            <v-btn color="warning" text @click="endSession">End Session</v-btn>
          </v-card-actions>
        </v-card>
      </v-dialog>
    </div>
  </div>
</template>

<script>
export default {
  layout: 'project',
  middleware: ['check-auth', 'auth', 'setCurrentProject'],

  data() {
    return {
      dialogCreateVote: false,
      dialogCreateSession: false,
      dialogConfirm: false,
      dialogEndSession: false,
      showErrors: false,
      sessions: [],
      selectedSession: null,
      sessionVotes: [],
      sessionMessages: [],
      newVote: {
        title: '',
        description: '',
        options: []
      },
      newSession: {
        title: '',
        description: ''
      },
      newMessage: '',
      error: false,
      errorMessage: '',
      messagePolling: null
    };
  },

  computed: {
    projectId() {
      return this.$route.params.id;
    },
    hasVotes() {
      return this.sessionVotes && this.sessionVotes.length > 0;
    },
    isAdmin() {
      // Check if user is a project admin or superuser
      // const role = this.$store.state.projects.userRole;
      return true;
    }
  },

  created() {
    this.fetchSessions();
  },

  beforeDestroy() {
    // Clear the interval when component is destroyed
    if (this.messagePolling) {
      clearInterval(this.messagePolling);
    }
  },

  methods: {
    async fetchSessions() {
      try {
        const response = await this.$axios.get(`/v1/projects/${this.projectId}/sessions`);
        this.sessions = response.data;
      } catch (error) {
        console.error('Error fetching sessions:', error);
        this.showError('Failed to load sessions. Please try again later.');
      }
    },

    selectSession(session) {
      this.selectedSession = session;
      this.fetchSessionVotes();
      this.fetchSessionMessages();
      
      // Set up polling to refresh messages periodically
      this.messagePolling = setInterval(() => {
        this.fetchSessionMessages();
      }, 5000); // Every 5 seconds
    },

    backToSessions() {
      this.selectedSession = null;
      
      // Clear the interval when leaving a session
      if (this.messagePolling) {
        clearInterval(this.messagePolling);
        this.messagePolling = null;
      }
    },

    async fetchSessionVotes() {
      if (!this.selectedSession) return;
      
      try {
        const response = await this.$axios.get(
          `/v1/projects/${this.projectId}/sessions/${this.selectedSession.id}/votes`
        );
        this.sessionVotes = response.data;
      } catch (error) {
        console.error('Error fetching votes:', error);
        this.showError('Failed to load votes. Please try again later.');
      }
    },

    async fetchSessionMessages() {
      if (!this.selectedSession) return;
      
      try {
        const response = await this.$axios.get(
          `/v1/projects/${this.projectId}/sessions/${this.selectedSession.id}/chat`
        );
        this.sessionMessages = response.data;
        
        // Scroll to bottom of chat after messages load
        this.$nextTick(() => {
          if (this.$refs.chatContainer) {
            this.$refs.chatContainer.scrollTop = this.$refs.chatContainer.scrollHeight;
          }
        });
      } catch (error) {
        console.error('Error fetching messages:', error);
      }
    },

    openCreateSessionDialog() {
      console.log('Opening session dialog');
      this.dialogCreateSession = true;
      this.$nextTick(() => {
        console.log('Dialog state:', this.dialogCreateSession);
      });
    },

    closeSessionDialog() {
      this.dialogCreateSession = false;
      this.showErrors = false;
      this.newSession = {
        title: '',
        description: ''
      };
    },

    async saveSession() {
      this.showErrors = true;
      if (!this.newSession.title) {
        return;
      }

      try {
        const response = await this.$axios.post(
          `/v1/projects/${this.projectId}/sessions`, 
          this.newSession
        );
        
        this.sessions.push(response.data);
        this.closeSessionDialog();
        this.showError('Session created successfully!', 'success');
      } catch (error) {
        console.error('Error saving session:', error);
        this.showError('Failed to create session. Please try again later.');
      }
    },

    confirmDeleteSession() {
      this.dialogConfirm = true;
    },

    async deleteSession() {
      if (!this.selectedSession) {
        this.dialogConfirm = false;
        return;
      }
      
      try {
        await this.$axios.delete(
          `/v1/projects/${this.projectId}/sessions/${this.selectedSession.id}`
        );
        
        this.dialogConfirm = false;
        this.backToSessions();
        this.fetchSessions();
      } catch (error) {
        console.error('Error deleting session:', error);
        this.showError('Failed to delete session. Please try again later.');
      }
    },

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

    async saveVote() {
      this.showErrors = true;
      if (!this.newVote.title || !this.newVote.options || this.newVote.options.length === 0) {
        return;
      }

      try {
        await this.$axios.post(
          `/v1/projects/${this.projectId}/sessions/${this.selectedSession.id}/votes`,
          this.newVote
        );
        
        this.closeVoteDialog();
        this.fetchSessionVotes();
      } catch (error) {
        console.error('Error saving vote:', error);
        this.showError('Failed to create vote. Please try again later.');
      }
    },

    async submitVote(voteId, option) {
      try {
        await this.$axios.post(
          `/v1/projects/${this.projectId}/sessions/${this.selectedSession.id}/votes/${voteId}/submit`,
          { option }
        );
        
        // Refresh votes to show updated results
        this.fetchSessionVotes();
      } catch (error) {
        console.error('Error submitting vote:', error);
        this.showError('Failed to submit your vote. Please try again later.');
      }
    },

    async sendMessage() {
      if (!this.newMessage.trim()) return;
      
      try {
        await this.$axios.post(
          `/v1/projects/${this.projectId}/sessions/${this.selectedSession.id}/chat`,
          { message: this.newMessage.trim() }
        );
        
        // Clear the input field
        this.newMessage = '';
        
        // Refresh messages to show the newly added message
        this.fetchSessionMessages();
      } catch (error) {
        console.error('Error sending message:', error);
        this.showError('Failed to send message. Please try again later.');
      }
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
        hash = ((hash << 5) - hash) + username.charCodeAt(i);
        hash = hash & hash; // Convert to 32bit integer
      }
      
      // Use the hash to pick a color from our palette
      const index = Math.abs(hash) % colors.length;
      return colors[index];
    },

    formatDate(dateString) {
      if (!dateString) return '';
      
      const date = new Date(dateString);
      return date.toLocaleDateString();
    },

    formatTime(dateString) {
      if (!dateString) return '';
      
      const date = new Date(dateString);
      return date.toLocaleTimeString();
    },

    showError(message) {
      this.error = true;
      this.errorMessage = message;
      
      // Hide error after 5 seconds
      setTimeout(() => {
        this.error = false;
      }, 5000);
    },

    confirmEndSession() {
      this.dialogEndSession = true;
    },

    async endSession() {
      if (!this.selectedSession) {
        this.dialogEndSession = false;
        return;
      }
      
      try {
        await this.$axios.patch(
          `/v1/projects/${this.projectId}/sessions/${this.selectedSession.id}`,
          { ended: true }
        );
        
        // Update local state
        this.selectedSession.ended = true;
        
        this.dialogEndSession = false;
        this.showError('Session ended successfully', 'success');
      } catch (error) {
        console.error('Error ending session:', error);
        this.showError('Failed to end session. Please try again later.');
      }
    },
  }
};
</script>

<style scoped>
.chat-messages {
  border: 1px solid #e0e0e0;
  border-radius: 4px;
  padding: 12px;
  background-color: #f9f9f9;
}
</style>