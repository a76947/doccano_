<template>
  <v-card>
    <v-card-title>
      <v-btn class="text-capitalize" color="primary" @click.stop="dialogCreateGroup = true">
        Create Perspective Group
      </v-btn>
      <v-btn class="text-capitalize ms-2" :disabled="!canDelete" outlined>
        Delete
      </v-btn>

      <!-- Group Creation Dialog -->
      <v-dialog v-model="dialogCreateGroup" max-width="500px">
        <v-card>
          <v-card-title class="headline">New Perspective Group</v-card-title>
          <v-card-text>
            <v-text-field
              v-model="editedGroup.name"
              label="Name"
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
          <v-card-title class="headline">Add Question to {{ currentGroup?.name }}</v-card-title>
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
              :items="['string', 'int', 'boolean', 'opções']"
              label="Data Type"
              :error="showErrors && !editedQuestion.data_type"
              :error-messages="showErrors && !editedQuestion.data_type ? ['* Required field'] : []"
              required
            />

            <v-combobox
              v-if="editedQuestion.data_type === 'opções'"
              v-model="editedQuestion.options"
              label="Options"
              multiple
              chips
              deletable-chips
              clearable
              :error="showErrors && editedQuestion.options.length === 0"
              :error-messages="showErrors 
              && editedQuestion.options.length === 0 ? ['* Required field'] : []"
            />
          </v-card-text>
          <v-card-actions>
            <v-spacer />
            <v-btn text @click="closeQuestionDialog">Cancel</v-btn>
            <v-btn color="primary" text @click="saveQuestion">Save</v-btn>
          </v-card-actions>
        </v-card>
      </v-dialog>
    </v-card-title>

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

    <!-- List of Perspective Groups -->
    <v-expansion-panels>
      <v-expansion-panel v-for="group in perspectiveGroups" :key="group.id">
        <v-expansion-panel-header>
          <div class="d-flex align-center">
            <span class="font-weight-bold">{{ group.name }}</span>
            <v-spacer></v-spacer>
            <v-btn 
              icon 
              small 
              class="mr-2"
              @click.stop="openAddQuestionDialog(group)"
            >
              <v-icon small>mdi-plus</v-icon>
            </v-btn>
          </div>
        </v-expansion-panel-header>
        <v-expansion-panel-content>
          <div class="mb-2">
            <em>{{ group.description }}</em>
          </div>
          
          <v-simple-table v-if="group.questions && group.questions.length > 0">
            <template v-slot:default>
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
                  <td>
                    <v-btn icon small @click.stop="showQuestionDetails(question)">
                      <v-icon small>mdi-eye</v-icon>
                    </v-btn>
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

    <!-- Question Details Dialog -->
    <v-dialog v-model="dialogDetails" max-width="500px">
      <v-card v-if="selectedPerspective">
        <v-card-title class="headline">Question Details</v-card-title>
        <v-card-text>
          <v-list-item>
            <v-list-item-content>
              <v-list-item-title>Question:</v-list-item-title>
              <v-list-item-subtitle>{{ selectedPerspective.question }}</v-list-item-subtitle>
            </v-list-item-content>
          </v-list-item>
          
          <v-list-item>
            <v-list-item-content>
              <v-list-item-title>Data Type:</v-list-item-title>
              <v-list-item-subtitle>{{ selectedPerspective.data_type }}</v-list-item-subtitle>
            </v-list-item-content>
          </v-list-item>
          
          <v-list-item v-if="selectedPerspective.options && selectedPerspective.options.length">
            <v-list-item-content>
              <v-list-item-title>Options:</v-list-item-title>
              <v-chip-group column>
                <v-chip v-for="(option, i) in selectedPerspective.options" :key="i" small>
                  {{ option }}
                </v-chip>
              </v-chip-group>
            </v-list-item-content>
          </v-list-item>
        </v-card-text>
        <v-card-actions>
          <v-spacer></v-spacer>
          <v-btn color="primary" text @click="dialogDetails = false">Close</v-btn>
        </v-card-actions>
      </v-card>
    </v-dialog>
  </v-card>
</template>

<script>
import { usePerspectiveApplicationService } from '@/services/application/perspective/perspectiveApplicationService'

export default {
  layout: 'project',
  middleware: ['check-auth', 'auth', 'setCurrentProject', 'isProjectAdmin'],

  validate({ params }) {
    return /^\d+$/.test(params.id)
  },

  data() {
    return {
      dialogCreateGroup: false,
      dialogCreateQuestion: false,
      dialogDetails: false,
      snackbar: false,
      snackbarMessage: '',
      snackbarError: false,
      snackbarErrorMessage: '',
      showErrors: false,
      currentGroup: null,
      perspectiveGroups: [],
      selected: [],
      selectedPerspective: null,

      editedGroup: {
        name: '',
        description: ''
      },
      
      editedQuestion: {
        question: '',
        data_type: 'string',
        options: []
      }
    }
  },

  computed: {
    projectId() {
      return this.$route.params.id
    },
    
    canDelete() {
      return this.selected.length > 0
    }
  },

  mounted() {
    this.fetchPerspectiveGroups()
  },

  methods: {
    async fetchPerspectiveGroups() {
      try {
        const service = usePerspectiveApplicationService()
        const response = await service.listPerspectiveGroups(this.projectId)
        this.perspectiveGroups = response.results
      } catch (err) {
        console.error('Error fetching perspective groups', err)
        this.snackbarErrorMessage = 'Failed to load perspective groups'
        this.snackbarError = true
      }
    },

    openAddQuestionDialog(group) {
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

    async saveGroup() {
      this.showErrors = true
      if (!this.editedGroup.name) {
        return
      }

      try {
        const service = usePerspectiveApplicationService()
        await service.createPerspectiveGroup(this.projectId, this.editedGroup)
        
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

      if (
        this.editedQuestion.data_type === 'opções' &&
        (!this.editedQuestion.options || this.editedQuestion.options.length === 0)
      ) {
        return
      }

      const payload = { ...this.editedQuestion, group_id: this.currentGroup.id }

      if (payload.data_type === 'boolean') {
        payload.options = ['true', 'false']
      } else if (payload.data_type !== 'opções') {
        payload.options = []
      }

      if (payload.data_type === 'opções') {
        payload.data_type = 'string'
      }

      try {
        const service = usePerspectiveApplicationService()
        await service.createPerspective(this.projectId, payload)
        
        this.snackbarMessage = 'Question added successfully!'
        this.snackbar = true
        this.closeQuestionDialog()
        this.fetchPerspectiveGroups()
      } catch (e) {
        this.snackbarErrorMessage = e.response?.data?.detail || 'Error adding question'
        this.snackbarError = true
      }
    },

    showQuestionDetails(question) {
      this.selectedPerspective = question
      this.dialogDetails = true
    }
  }
}
</script>