<template>
  <v-card>
    <v-card-title>
      <template v-if="!hasGroups">
        <v-btn 
          class="text-capitalize" 
          color="primary" 
          @click.stop="openCreateGroupDialog()"
          v-if="isAdmin"
        >
          Create Perspective Group
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
              Create Perspective Group
            </v-btn>
          </template>
          <span>Only administrators can create perspective groups</span>
        </v-tooltip>
        <v-alert
          v-if="!isAdmin"
          type="error"
          dense
          class="mt-2"
        >
          You do not have permission to create perspective groups. Please contact an administrator.
        </v-alert>
      </template>
      <v-alert
        v-else
        type="info"
        dense
        class="mb-0"
      >
        Only one perspective group is allowed per project
      </v-alert>
    </v-card-title>

    <v-card-subtitle v-if="devMode" class="pa-2">
      <v-chip-group
        v-model="userRole"
        mandatory
        column
      >
        <v-chip 
          value="admin"
          :color="userRole === 'admin' ? 'primary' : ''"
          @click="userRole = 'admin'"
        >
          Admin Mode
        </v-chip>
        <v-chip
          value="annotator"
          :color="userRole === 'annotator' ? 'success' : ''" 
          @click="userRole = 'annotator'"
        >
          Annotator Mode
        </v-chip>
        <v-chip
          value="viewer"
          :color="userRole === 'viewer' ? 'info' : ''"
          @click="userRole = 'viewer'"
        >
          Viewer Mode
        </v-chip>
      </v-chip-group>
    </v-card-subtitle>

    <!-- Group Creation Dialog -->
    <v-dialog v-model="dialogCreateGroup" max-width="500px">
      <v-card>
        <v-card-title class="headline">Create Perspective Group</v-card-title>
        <v-card-text>
          <v-text-field
            v-model="editedGroup.name"
            label="Group Name"
            :error="showErrors && !editedGroup.name"
            :error-messages="showErrors && !editedGroup.name ? ['* Required field'] : []"
            required
          />
          <v-textarea
            v-model="editedGroup.description"
            label="Description"
            rows="3"
          />
        </v-card-text>
        <v-card-actions>
          <v-spacer />
          <v-btn text @click="closeGroupDialog">Cancel</v-btn>
          <v-btn color="primary" text @click="saveGroup">Save</v-btn>
        </v-card-actions>
      </v-card>
    </v-dialog>

    <!-- Question Creation Dialog -->
    <v-dialog v-model="dialogCreateQuestion" max-width="500px">
      <v-card>
        <v-card-title class="headline">Add New Question</v-card-title>
        <v-card-text>
          <v-text-field
            v-model="editedQuestion.question"
            label="Question"
            :error="showErrors && !editedQuestion.question"
            :error-messages="showErrors && !editedQuestion.question ? ['* Required field'] : []"
            required
          />
          <v-select
            v-model="editedQuestion.data_type"
            :items="dataTypes"
            label="Data Type"
            :error="showErrors && !editedQuestion.data_type"
            :error-messages="showErrors && !editedQuestion.data_type ? ['* Required field'] : []"
            required
          />

          <!-- Options section - visible for string or int types -->
          <div v-if="editedQuestion.data_type === 'string' || editedQuestion.data_type === 'int'">
            <div class="d-flex align-center mb-2">
              <h3 class="subtitle-1">Answer Options</h3>
              <v-spacer></v-spacer>
              <v-btn small color="primary" @click="addOption">
                <v-icon small left>mdi-plus</v-icon> Add Option
              </v-btn>
            </div>
            
            <v-alert
              v-if="showErrors && (editedQuestion.data_type === 'string' 
              || editedQuestion.data_type === 'int') && editedQuestion.options.length === 0"
              dense
              type="error"
              class="mb-3"
            >
              Please add at least one answer option
            </v-alert>
            
            <div v-for="(option, index) in editedQuestion.options" :key="index" class="mb-2 d-flex">
              <v-text-field
                v-model="editedQuestion.options[index]"
                :label="`Option ${index + 1}`"
                hide-details
                class="mr-2"
              />
              <v-btn icon color="error" @click="removeOption(index)">
                <v-icon small>mdi-delete</v-icon>
              </v-btn>
            </div>
          </div>

          <!-- Boolean type doesn't need options as it's always Yes/No -->
          <v-alert
            v-if="editedQuestion.data_type === 'boolean'"
            type="info"
            dense
            class="mt-2"
          >
            Boolean questions will have Yes/No answer options automatically.
          </v-alert>
        </v-card-text>
        <v-card-actions>
          <v-spacer />
          <v-btn text @click="closeQuestionDialog">Cancel</v-btn>
          <v-btn color="primary" text @click="saveQuestion">Save</v-btn>
        </v-card-actions>
      </v-card>
    </v-dialog>

    <!-- Check if there are perspective groups before rendering expansion panels -->
    <div v-if="!hasGroups" class="text-center pa-5">
      No perspective groups yet. Click "Create Perspective Group" to add one.
    </div>

    <!-- List of Perspective Groups -->
    <v-expansion-panels v-else>
      <v-expansion-panel 
        v-for="group in validGroups" 
        :key="group.id"
      >
        <v-expansion-panel-header>
          <div class="d-flex align-center">
            <span class="font-weight-bold">{{ group.name }}</span>
            <v-spacer></v-spacer>
            <!-- Add Question button -->
            <v-btn 
              color="primary"
              small
              class="mr-2"
              @click.stop="openAddQuestionDialog(group)"
              v-if="isAdmin"
            >
              <v-icon left small>mdi-plus</v-icon>
              Add Question
            </v-btn>
            <v-tooltip v-else bottom>
              <template #activator="{ on, attrs }">
                <v-btn 
                  color="primary"
                  small
                  class="mr-2"
                  disabled
                  v-bind="attrs"
                  v-on="on"
                >
                  <v-icon left small>mdi-plus</v-icon>
                  Add Question
                </v-btn>
              </template>
              <span>Only administrators can add questions</span>
            </v-tooltip>
            <!-- Answer Questions button -->
            <v-btn 
              color="success"
              small
              class="mr-2"
              :disabled="!hasQuestions(group)"
              @click.stop="openAnswerQuestionsDialog(group)"
            >
              <v-icon left small>mdi-text-box-check-outline</v-icon>
              Answer
            </v-btn>
          </div>
        </v-expansion-panel-header>
        <v-expansion-panel-content>
          <div class="mb-2">
            <em>{{ group.description }}</em>
          </div>
          
          <v-simple-table v-if="hasQuestions(group)">
            <template #default>
              <thead>
                <tr>
                  <th>Question</th>
                  <th>Data Type</th>
                  <th>Actions</th>
                </tr>
              </thead>
              <tbody>
                <tr v-for="question in group.questions" :key="question.id">
                  <td>{{ question.question }}</td>
                  <td>{{ question.data_type }}</td>
                  <td class="text-center">
                    <div class="d-flex justify-end">
                      <v-btn 
                        icon 
                        color="primary"
                        class="mx-1" 
                        @click.stop="showQuestionDetails(question)"
                      >
                        <v-icon>mdi-eye</v-icon>
                      </v-btn>
                      
                      <!-- Add this button for viewing responses -->
                      <v-btn 
                        v-if="isAdmin"
                        color="info"
                        class="mx-1"
                        small
                        @click.stop="showQuestionResponses(question)"
                      >
                        <v-icon left small>mdi-poll</v-icon>
                        Responses
                      </v-btn>
                      
                      <v-btn 
                        v-if="isAdmin"
                        color="error"
                        class="mx-1"
                        small
                        @click.stop="confirmDeleteQuestion(question)"
                      >
                        <v-icon left small>mdi-delete</v-icon>
                        Delete
                      </v-btn>
                    </div>
                  </td>
                </tr>
              </tbody>
            </template>
          </v-simple-table>
          <div v-else class="text-center pa-3">
            No questions yet. Click + to add.
          </div>
        </v-expansion-panel-content>
      </v-expansion-panel>
    </v-expansion-panels>

    <!-- Add a new dialog for answering questions -->
    <v-dialog v-model="dialogAnswerQuestions" max-width="600px">
      <v-card>
        <v-card-title class="headline">
          Answer Questions for {{ currentGroup?.name }}
        </v-card-title>
        <v-card-text>
          <form @submit.prevent="saveAnswers">
            <div v-for="question in currentGroup?.questions" :key="question.id" class="mb-4">
              <h3 class="subtitle-1 mb-2">{{ question.question }}</h3>
              
              <!-- String type questions with options -->
              <v-radio-group
                v-if="question.data_type === 'string'"
                v-model="questionAnswers[question.id]"
                :mandatory="false"
              >
                <v-radio
                  v-for="option in question.options"
                  :key="option"
                  :label="option"
                  :value="option"
                ></v-radio>
              </v-radio-group>
              
              <!-- Integer type questions with options -->
              <v-radio-group
                v-else-if="question.data_type === 'int'"
                v-model="questionAnswers[question.id]"
                :mandatory="false"
              >
                <v-radio
                  v-for="option in question.options"
                  :key="option"
                  :label="option"
                  :value="option"
                ></v-radio>
              </v-radio-group>
              
              <!-- Boolean type questions (Yes/No) -->
              <v-radio-group
                v-else-if="question.data_type === 'boolean'"
                v-model="questionAnswers[question.id]"
                :mandatory="false"
              >
                <v-radio
                  label="Yes"
                  :value="true"
                ></v-radio>
                <v-radio
                  label="No"
                  :value="false"
                ></v-radio>
              </v-radio-group>
            </div>
          </form>
        </v-card-text>
        <v-card-actions>
          <v-spacer />
          <v-btn text @click="closeAnswerDialog">Cancel</v-btn>
          <v-btn color="success" @click="saveAnswers">Submit Answers</v-btn>
        </v-card-actions>
      </v-card>
    </v-dialog>
    
    <!-- Add this dialog after your other dialogs, before the closing </v-card> tag -->
    <v-dialog v-model="dialogConfirmDelete" max-width="400px">
      <v-card>
        <v-card-title class="headline">Delete Question</v-card-title>
        <v-card-text>
          Are you sure you want to delete the question 
          <strong>{{ questionToDelete?.question }}</strong>?
          This action cannot be undone.
        </v-card-text>
        <v-card-actions>
          <v-spacer></v-spacer>
          <v-btn text @click="dialogConfirmDelete = false">Cancel</v-btn>
          <v-btn color="error" text @click="deleteQuestion">Delete</v-btn>
        </v-card-actions>
      </v-card>
    </v-dialog>

    <!-- Add this dialog for viewing responses after your 
     other dialogs but before the closing </v-card> tag -->
    <v-dialog v-model="dialogViewResponses" max-width="700px">
      <v-card>
        <v-card-title class="headline d-flex align-center">
          <span>Responses for Question</span>
          <v-spacer></v-spacer>
          <v-chip color="primary" class="ml-2">{{ currentQuestion?.question }}</v-chip>
        </v-card-title>
        
        <v-card-text v-if="loadingResponses">
          <div class="text-center pa-4">
            <v-progress-circular indeterminate color="primary"></v-progress-circular>
            <div class="mt-2">Loading responses...</div>
          </div>
        </v-card-text>
        
        <v-card-text v-else-if="questionResponses.length === 0" class="text-center pa-4">
          <v-icon large color="grey lighten-1">mdi-poll-box-outline</v-icon>
          <div class="mt-2 grey--text">No responses for this question yet</div>
        </v-card-text>
        
        <template v-else>
          <!-- Chart view for overview -->
          <v-card-text>
            <h3 class="subtitle-1 mb-3">Response Summary</h3>
            <v-simple-table>
              <template #default>
                <thead>
                  <tr>
                    <th>Answer</th>
                    <th>Count</th>
                    <th>Percentage</th>
                  </tr>
                </thead>
                <tbody>
                  <tr v-for="(count, answer) in responseStats" :key="answer">
                    <td>{{ answer }}</td>
                    <td>{{ count }}</td>
                    <td>
                      {{ Math.round((count / questionResponses.length) * 100) }}%
                      <v-progress-linear
                        :value="(count / questionResponses.length) * 100"
                        height="6"
                        rounded
                        color="primary"
                        class="mt-1"
                      ></v-progress-linear>
                    </td>
                  </tr>
                </tbody>
              </template>
            </v-simple-table>
          </v-card-text>
          
          <!-- Detailed responses -->
          <v-card-text>
            <h3 class="subtitle-1 mb-3">Individual Responses</h3>
            <v-simple-table>
              <template #default>
                <thead>
                  <tr>
                    <th>User</th>
                    <th>Response</th>
                    <th>Date</th>
                  </tr>
                </thead>
                <tbody>
                  <tr v-for="response in questionResponses" :key="response.id || Math.random()">
                    <td>{{ response.created_by_username || 'Unknown User' }}</td>
                    <td>{{ response.answer || 'No answer' }}</td>
                    <td>{{ formatDate(response.created_at) }}</td>
                  </tr>
                </tbody>
              </template>
            </v-simple-table>
          </v-card-text>
        </template>
        
        <v-card-actions>
          <v-spacer></v-spacer>
          <v-btn text @click="dialogViewResponses = false">Close</v-btn>
        </v-card-actions>
      </v-card>
    </v-dialog>

    <!-- Snackbars -->
    <v-snackbar v-model="snackbar" timeout="3000" top color="success">
      {{ snackbarMessage }}
      <template #action="{ attrs }">
        <v-btn text v-bind="attrs" @click="snackbar = false">Close</v-btn>
      </template>
    </v-snackbar>
    
    <v-snackbar v-model="snackbarError" timeout="3000" top color="error">
      {{ snackbarErrorMessage }}
      <template #action="{ attrs }">
        <v-btn text v-bind="attrs" @click="snackbarError = false">Close</v-btn>
      </template>
    </v-snackbar>
  </v-card>
</template>

<script>
export default {
  layout: 'project',
  middleware: ['check-auth', 'auth', 'setCurrentProject'],

  data() {
    return {
      dialogCreateGroup: false,
      dialogCreateQuestion: false,
      dialogAnswerQuestions: false,
      snackbar: false,
      snackbarMessage: '',
      snackbarError: false,
      snackbarErrorMessage: '',
      showErrors: false,
      currentGroup: null,
      perspectiveGroups: [],
      questionAnswers: {},
      
      editedGroup: {
        name: '',
        description: ''
      },
      
      editedQuestion: {
        question: '',
        data_type: 'string',
        options: []
      },

      dataTypes: [
        { text: 'Text (with options)', value: 'string' },
        { text: 'Number (with options)', value: 'int' },
        { text: 'Yes/No', value: 'boolean' }
      ],

      dialogConfirmDelete: false,
      questionToDelete: null,

      // Development mode toggle
      devMode: false, // Set to false when deploying
      userRole: 'admin', // 'admin', 'annotator', 'viewer'

      userPermissions: null,
      loadingPermissions: false,

      // Add these to your existing data properties
      dialogViewResponses: false,
      currentQuestion: null,
      questionResponses: [],
      loadingResponses: false,
    }
  },

  computed: {
    projectId() {
      return this.$route.params.id
    },
    
    // Computed property to check if we have groups
    hasGroups() {
      return this.perspectiveGroups && this.perspectiveGroups.length > 0
    },
    
    // Computed property to filter out null groups
    validGroups() {
      return this.perspectiveGroups.filter(group => !!group)
    },

    // Add this to your computed properties
    isAdmin() {
  // For development mode, use the role selector
  if (this.devMode) {
    return this.userRole === 'admin'
  }
  
  // Log what we're checking
  console.log('Checking admin status with permissions:', this.userPermissions)
  
  // Use the permissions data from the API
  return this.userPermissions?.isAdmin === true
},

    // Add this computed property for response statistics
    responseStats() {
      const stats = {};
      
      if (!this.questionResponses.length) return stats;
      
      // Count occurrences of each answer
      this.questionResponses.forEach(response => {
        const answer = response.answer;
        if (!stats[answer]) {
          stats[answer] = 0;
        }
        stats[answer]++;
      });
      
      return stats;
    },
  },

  mounted() {
    this.fetchPerspectiveGroups();
    this.fetchUserPermissions();
  },

  methods: {
    async fetchPerspectiveGroups() {
      try {
        // Use the Vue 2 service pattern
        const response = await this.$services.perspective.listPerspectiveGroups(this.projectId)
        console.log('API response:', response) // Debug response
        this.perspectiveGroups = response.results || response || []
      } catch (err) {
        console.error('Error fetching perspective groups', err)
        this.snackbarErrorMessage = 'Failed to connect to the database, try again later'
        this.snackbarError = true
      }
    },
    
    // Helper method to check if a group has questions
    hasQuestions(group) {
      return group && group.questions && group.questions.length > 0
    },

    openAddQuestionDialog(group) {
      console.log("Opening question dialog, isAdmin:", this.isAdmin);
      
      // Check if user is admin before allowing to add questions
      if (!this.isAdmin) {
        this.snackbarErrorMessage = 'Only administrators can add questions'
        this.snackbarError = true
        return
      }
      
      this.currentGroup = group
      this.editedQuestion = {
        question: '',
        data_type: 'string',
        options: []
      }
      this.dialogCreateQuestion = true
    },

    closeGroupDialog() {
      this.dialogCreateGroup = false
      this.showErrors = false
      this.editedGroup = {
        name: '',
        description: ''
      }
    },

    closeQuestionDialog() {
      this.dialogCreateQuestion = false
      this.showErrors = false
      this.currentGroup = null
      this.editedQuestion = {
        question: '',
        data_type: 'string',
        options: []
      }
    },

    closeAnswerDialog() {
      this.dialogAnswerQuestions = false
      this.currentGroup = null
      this.questionAnswers = {}
    },

    async saveGroup() {
      this.showErrors = true
      if (!this.editedGroup.name) {
        return
      }

      try {
        await this.$services.perspective.createPerspectiveGroup(this.projectId, this.editedGroup)
        
        this.snackbarMessage = 'Perspective group created successfully!'
        this.snackbar = true
        this.closeGroupDialog()
        this.fetchPerspectiveGroups()
      } catch (e) {
        this.snackbarErrorMessage = e.response?.data?.detail || 'Error creating perspective group'
        this.snackbarError = true
      }
    },

    async saveQuestion() {
      this.showErrors = true
      if (!this.editedQuestion.question || !this.editedQuestion.data_type) {
        return
      }

      // Validate options for string and int types
      if ((this.editedQuestion.data_type === 'string' || this.editedQuestion.data_type === 'int') 
          && this.editedQuestion.options.length === 0) {
        return
      }
      
      // Filter out empty options
      const filteredOptions = this.editedQuestion.options.filter(opt => opt.trim() !== '')
      
      const payload = { 
        ...this.editedQuestion,
        options: filteredOptions,
        group: this.currentGroup.id,
        project: this.projectId,
        name: this.editedQuestion.question 
      }

      try {
        await this.$services.perspective.createPerspective(this.projectId, payload)
        
        this.snackbarMessage = 'Question added successfully!'
        this.snackbar = true
        this.closeQuestionDialog()
        this.fetchPerspectiveGroups()
      } catch (e) {
        console.error('Error adding question:', e.response?.data || e)
        this.snackbarErrorMessage = e.response?.data?.detail || 'Couldnt connect to the database, try again later'
        this.snackbarError = true
      }
    },
    
    async saveAnswers() {
      try {
        const answersToSave = []
        
        // Format answers for API submission
        for (const [questionId, answer] of Object.entries(this.questionAnswers)) {
          // Skip empty answers
          if (answer === null || answer === '') continue
          
          answersToSave.push({
            perspective: parseInt(questionId), // Convert to integer
            project: parseInt(this.projectId), // Convert to integer
            answer: String(answer)  // Convert all answers to strings for storage
          })
        }
        
        // Only proceed if we have answers
        if (answersToSave.length === 0) {
          this.snackbarErrorMessage = 'Please answer at least one question'
          this.snackbarError = true
          return
        }
        
        // Save each answer
        const savePromises = answersToSave.map(answer => 
          this.$services.perspective.createPerspectiveAnswer(this.projectId, answer)
        )
        
        await Promise.all(savePromises)
        
        this.snackbarMessage = 'Answers submitted successfully!'
        this.snackbar = true
        this.closeAnswerDialog()
      } catch (e) {
        console.error('Error saving answers:', e.response?.data || e)
        this.snackbarErrorMessage = e.response?.data?.detail || 'Error saving answers'
        this.snackbarError = true
      }
    },

    showQuestionDetails(question) {
      // Implement this method if needed
      console.log('Question details:', question)
    },

    addOption() {
      this.editedQuestion.options.push('')
    },

    removeOption(index) {
      this.editedQuestion.options.splice(index, 1)
    },

    openAnswerQuestionsDialog(group) {
      this.currentGroup = group
      this.questionAnswers = {}  // Reset the answers
      
      // Initialize answers for existing questions
      if (group && group.questions) {
        group.questions.forEach(question => {
          // Default values by question type
          if (question.data_type === 'boolean') {
            this.questionAnswers[question.id] = null
          } else {
            this.questionAnswers[question.id] = ''
          }
        })
      }
      
      this.dialogAnswerQuestions = true
    },

    confirmDeleteQuestion(question) {
      // Check if user is admin before allowing to delete questions
      if (!this.isAdmin) {
        this.snackbarErrorMessage = 'Only administrators can delete questions'
        this.snackbarError = true
        return
      }
      
      this.questionToDelete = question
      this.dialogConfirmDelete = true
    },

    async deleteQuestion() {
      if (!this.questionToDelete) return

      try {
        await this.$services.perspective.deletePerspective(
          this.projectId, 
          this.questionToDelete.id
        )
        
        this.snackbarMessage = 'Question deleted successfully!'
        this.snackbar = true
        this.dialogConfirmDelete = false
        this.questionToDelete = null
        this.fetchPerspectiveGroups() // Refresh the list
      } catch (e) {
        console.error('Error deleting question:', e.response?.data || e)
        this.snackbarErrorMessage = e.response?.data?.detail || 'Error deleting question'
        this.snackbarError = true
      }
    },

    openCreateGroupDialog() {
      if (this.hasGroups) {
        this.snackbarErrorMessage = 'Only one perspective group is allowed per project'
        this.snackbarError = true
        return
      }
      this.dialogCreateGroup = true
    },

    async fetchUserPermissions() {
      try {
        this.loadingPermissions = true
        // Call your API to get user permissions for this project
        const response = await this.$axios.get(`/v1/projects/${this.projectId}/my-permissions/`)
        console.log('User permissions response:', response.data)
        
        // Save the permissions data
        this.userPermissions = response.data
      } catch (error) {
        console.error('Error fetching user permissions:', error)
        this.snackbarErrorMessage = 'Could not verify your permissions'
        this.snackbarError = true
      } finally {
        this.loadingPermissions = false
      }
    },

    // Show all responses for a question
    async showQuestionResponses(question) {
      if (!this.isAdmin) {
        this.snackbarErrorMessage = 'Only administrators can view all responses';
        this.snackbarError = true;
        return;
      }
      
      this.currentQuestion = question;
      this.dialogViewResponses = true;
      this.loadingResponses = true;
      this.questionResponses = [];
      
      try {
        // Change this line to use the correct method
        const response = await this.$services.perspective.listPerspectiveAnswersByQuestion(
          this.projectId, 
          question.id
        );
        this.questionResponses = response.results || response || [];
        console.log('Question responses:', this.questionResponses);
      } catch (error) {
        console.error('Error loading responses:', error);
        this.snackbarErrorMessage = 'Failed to connect to the database, try again later';
        this.snackbarError = true;
      } finally {
        this.loadingResponses = false;
      }
    },

    // Add this method for formatting dates
    formatDate(dateString) {
      if (!dateString) return 'N/A';
      
      try {
        const date = new Date(dateString);
        // Check if date is valid
        if (isNaN(date.getTime())) {
          return 'Invalid Date';
        }
        return date.toLocaleDateString() + ' ' + date.toLocaleTimeString();
      } catch (error) {
        console.error('Error formatting date:', error);
        return 'N/A';
      }
    },
  }
}
</script>