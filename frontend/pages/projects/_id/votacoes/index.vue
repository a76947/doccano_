<template>
  <v-card>
    <v-card-title>
      <template v-if="!hasVotes">
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
      </template>
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
      <v-card-title>Chat</v-card-title>
      <v-card-text>
        <div v-for="(message, index) in messages" :key="index" class="mb-2">
          <strong>{{ message.user }}:</strong> {{ message.text }}
        </div>
        <v-textarea
          v-model="newMessage"
          label="Type your message"
          rows="2"
          outlined
        />
        <v-btn class="mt-2" color="primary" @click="sendMessage">Send</v-btn>
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
      messages: [],
      newMessage: ''
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

  mounted() {
    this.fetchVotes();
    this.loadMessagesFromLocalStorage();
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
        this.votes.push({
          ...this.newVote,
          id: Date.now(),
          results: this.newVote.options.reduce((acc, option) => {
            acc[option] = 0;
            return acc;
          }, {})
        });
        this.closeVoteDialog();
      } catch (error) {
        console.error('Error saving vote:', error);
      }
    },
    openVoteDialog(vote) {
      console.log('Vote dialog opened for:', vote);
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
    submitVote(voteId, option) {
      const vote = this.votes.find(v => v.id === voteId);
      if (vote) {
        vote.results[option] += 1;
      }
    },
    loadMessagesFromLocalStorage() {
      const storageKey = `chat_messages_${this.projectId}`;
      const savedMessages = localStorage.getItem(storageKey);
      this.messages = savedMessages ? JSON.parse(savedMessages) : [];
    },
    sendMessage() {
      if (this.newMessage.trim()) {
        const storageKey = `chat_messages_${this.projectId}`;
        
        if (!Array.isArray(this.messages)) {
          this.messages = [];
        }
        
        // Get the current username from the store
        const currentUsername = this.$store.state.auth.username || 'Anonymous';
        
        const message = {
          user: currentUsername, // Use the actual username
          text: this.newMessage.trim(),
          timestamp: new Date().toISOString()
        };
        
        this.messages.push(message);
        localStorage.setItem(storageKey, JSON.stringify(this.messages));
        this.newMessage = '';
      }
    }
  }
};
</script>