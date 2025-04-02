<template>
  <v-card>
    <v-card-title>
      <v-btn 
        class="text-capitalize" 
        color="primary" 
        @click.stop="openCreateGroupDialog()"
        v-if="!hasGroups"
      >
        Create Perspective Group
      </v-btn>
      <v-alert
        v-else
        type="info"
        dense
        class="mb-0"
      >
        Only one perspective group is allowed per project
      </v-alert>
    </v-card-title>

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
              v-if="showErrors 
                && (editedQuestion.data_type === 'string' || editedQuestion.data_type === 'int') 
                && editedQuestion.options.length === 0"
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
              <!-- Botão para remover essa opção -->
              <v-btn icon color="error" dark @click="removeOption(index)">
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

    <!-- Question Editing Dialog -->
    <v-dialog v-model="dialogEditQuestion" max-width="500px">
      <v-card>
        <v-card-title class="headline">Edit Question</v-card-title>
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

          <!-- Options visible for string/int -->
          <div v-if="editedQuestion.data_type === 'string' || editedQuestion.data_type === 'int'">
            <div class="d-flex align-center mb-2">
              <h3 class="subtitle-1">Answer Options</h3>
              <v-spacer></v-spacer>
              <v-btn small color="primary" @click="addOption">
                <v-icon small left>mdi-plus</v-icon> Add Option
              </v-btn>
            </div>

            <v-alert
              v-if="showErrors && editedQuestion.options.length === 0"
              dense
              type="error"
              class="mb-3"
            >
              Please add at least one answer option
            </v-alert>

            <div
              v-for="(option, index) in editedQuestion.options"
              :key="index"
              class="mb-2 d-flex"
            >
              <v-text-field
                v-model="editedQuestion.options[index]"
                :label="`Option ${index + 1}`"
                hide-details
                class="mr-2"
              />
              <!-- Botão para remover essa opção -->
              <v-btn icon color="error" dark @click="removeOption(index)">
                <v-icon small>mdi-delete</v-icon>
              </v-btn>
            </div>
          </div>

          <!-- Boolean info -->
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
          <v-btn text @click="closeEditQuestionDialog">Cancel</v-btn>
          <v-btn color="primary" text @click="saveEditedQuestion">Save Changes</v-btn>
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
            >
              <v-icon left small>mdi-plus</v-icon>
              Add Question
            </v-btn>
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

                      <!-- Botão Edit -->
                      <v-btn
                        color="warning"
                        class="mx-1"
                        small
                        @click.stop="openEditQuestionDialog(group, question)"
                      >
                        <v-icon left small>mdi-pencil</v-icon>
                        Edit
                      </v-btn>
                      
                      <v-btn 
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

    <!-- Dialog for answering questions -->
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
    
    <!-- Confirm Delete Dialog -->
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
  middleware: ['check-auth', 'auth', 'setCurrentProject', 'isProjectAdmin'],

  data() {
    return {
      dialogCreateGroup: false,
      dialogCreateQuestion: false,
      dialogEditQuestion: false,
      dialogAnswerQuestions: false,
      dialogConfirmDelete: false,

      // Variáveis de estado e dados
      perspectiveGroups: [],
      questionAnswers: {},
      questionToDelete: null,
      currentGroup: null,

      // Para controlar validações e mensagens
      showErrors: false,
      snackbar: false,
      snackbarMessage: '',
      snackbarError: false,
      snackbarErrorMessage: '',

      // Objetos para criação/edição
      editedGroup: {
        name: '',
        description: ''
      },
      editedQuestion: {
        id: null,
        question: '',
        data_type: 'string',
        options: []
      },

      // Tipos de dados possíveis
      dataTypes: [
        { text: 'Text (with options)', value: 'string' },
        { text: 'Number (with options)', value: 'int' },
        { text: 'Yes/No', value: 'boolean' }
      ]
    }
  },

  computed: {
    projectId() {
      return this.$route.params.id
    },
    hasGroups() {
      return this.perspectiveGroups && this.perspectiveGroups.length > 0
    },
    validGroups() {
      return this.perspectiveGroups.filter(group => !!group)
    }
  },

  mounted() {
    this.fetchPerspectiveGroups()
  },

  methods: {
    // ---------------------------------------------------------------------
    // LISTAR GROUPS
    // ---------------------------------------------------------------------
    async fetchPerspectiveGroups() {
      try {
        const response = await this.$services.perspective.listPerspectiveGroups(this.projectId)
        console.log('API response:', response)
        this.perspectiveGroups = response.results || response || []
      } catch (err) {
        console.error('Error fetching perspective groups', err)

        if (!err.response) {
          this.snackbarErrorMessage = 'De momento não é possivel realizar esta operação.'
        } else if (err.response.status >= 500) {
          this.snackbarErrorMessage = 'De momento não é possivel realizar esta operação.'
        } else {
          this.snackbarErrorMessage = err.response.data?.detail 
            || 'De momento não é possivel realizar esta operação.'
        }
        this.snackbarError = true
      }
    },

    hasQuestions(group) {
      return group && group.questions && group.questions.length > 0
    },

    // ---------------------------------------------------------------------
    // CRIAR GROUP
    // ---------------------------------------------------------------------
    openCreateGroupDialog() {
      if (this.hasGroups) {
        this.snackbarErrorMessage = 'Only one perspective group is allowed per project'
        this.snackbarError = true
        return
      }
      this.dialogCreateGroup = true
    },
    closeGroupDialog() {
      this.dialogCreateGroup = false
      this.showErrors = false
      this.editedGroup = { name: '', description: '' }
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
        console.error('Error creating perspective group', e)
        if (!e.response) {
          this.snackbarErrorMessage = 'De momento não é possivel realizar esta operação.'
        } else if (e.response.status >= 500) {
          this.snackbarErrorMessage = 'De momento não é possivel realizar esta operação.'
        } else {
          this.snackbarErrorMessage = e.response.data?.detail || 'Error creating perspective group'
        }
        this.snackbarError = true
      }
    },

    // ---------------------------------------------------------------------
    // CRIAR PERGUNTA
    // ---------------------------------------------------------------------
    openAddQuestionDialog(group) {
      this.currentGroup = group
      this.editedQuestion = {
        id: null,
        question: '',
        data_type: 'string',
        options: []
      }
      this.dialogCreateQuestion = true
    },
    closeQuestionDialog() {
      this.dialogCreateQuestion = false
      this.showErrors = false
      this.currentGroup = null
      this.editedQuestion = { id: null, question: '', data_type: 'string', options: [] }
    },
    async saveQuestion() {
      this.showErrors = true

      // Verifica se "question" e "data_type" estão preenchidos
      if (!this.editedQuestion.question || !this.editedQuestion.data_type) {
        return
      }

      // Filtra opções vazias
      const filteredOptions = this.editedQuestion.options.filter(opt => opt.trim() !== '')

      // Se havia opções vazias
      if (filteredOptions.length < this.editedQuestion.options.length) {
        this.snackbarErrorMessage = 'Some options are empty. Please fill them or remove them.'
        this.snackbarError = true
        return
      }

      // Se for string/int, exige ao menos 1 opção
      if (
        (this.editedQuestion.data_type === 'string' || this.editedQuestion.data_type === 'int')
        && filteredOptions.length === 0
      ) {
        this.snackbarErrorMessage = 'Please add at least one answer option.'
        this.snackbarError = true
        return
      }

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
        console.error('Error adding question:', e)
        if (!e.response) {
          this.snackbarErrorMessage = 'De momento não é possivel realizar esta operação.'
        } else if (e.response.status >= 500) {
          this.snackbarErrorMessage = 'De momento não é possivel realizar esta operação.'
        } else {
          this.snackbarErrorMessage = e.response.data?.detail || 'Error adding question'
        }
        this.snackbarError = true
      }
    },

    // ---------------------------------------------------------------------
    // EDITAR PERGUNTA
    // ---------------------------------------------------------------------
    openEditQuestionDialog(group, question) {
      this.currentGroup = group
      this.editedQuestion = {
        id: question.id,
        question: question.question,
        data_type: question.data_type,
        options: question.options ? [...question.options] : []
      }
      this.dialogEditQuestion = true
    },
    closeEditQuestionDialog() {
      this.dialogEditQuestion = false
      this.showErrors = false
      this.currentGroup = null
      this.editedQuestion = { id: null, question: '', data_type: 'string', options: [] }
    },
    async saveEditedQuestion() {
      this.showErrors = true
      if (!this.editedQuestion.question || !this.editedQuestion.data_type) {
        return
      }

      // Filtra opções vazias
      const filteredOptions = this.editedQuestion.options.filter(opt => opt.trim() !== '')

      // Se havia opções vazias
      if (filteredOptions.length < this.editedQuestion.options.length) {
        this.snackbarErrorMessage = 'Some options are empty. Please fill them or remove them.'
        this.snackbarError = true
        return
      }

      // Se for string/int, exige ao menos 1 opção
      if (
        (this.editedQuestion.data_type === 'string' || this.editedQuestion.data_type === 'int')
        && filteredOptions.length === 0
      ) {
        this.snackbarErrorMessage = 'Please add at least one answer option.'
        this.snackbarError = true
        return
      }

      const payload = {
        ...this.editedQuestion,
        options: filteredOptions,
        group: this.currentGroup.id,
        project: this.projectId,
        name: this.editedQuestion.question
      }

      try {
        await this.$services.perspective.updatePerspective(
          this.projectId,
          this.editedQuestion.id,
          payload
        )
        this.snackbarMessage = 'Question updated successfully!'
        this.snackbar = true
        this.closeEditQuestionDialog()
        this.fetchPerspectiveGroups()
      } catch (e) {
        console.error('Error updating question:', e)
        if (!e.response) {
          this.snackbarErrorMessage = 'De momento não é possivel realizar esta operação.'
        } else if (e.response.status >= 500) {
          this.snackbarErrorMessage = 'De momento não é possivel realizar esta operação.'
        } else {
          this.snackbarErrorMessage = e.response.data?.detail || 'Error updating question'
        }
        this.snackbarError = true
      }
    },

    // ---------------------------------------------------------------------
    // RESPONDER PERGUNTAS
    // ---------------------------------------------------------------------
    openAnswerQuestionsDialog(group) {
      this.currentGroup = group
      this.questionAnswers = {}
      if (group && group.questions) {
        group.questions.forEach(question => {
          if (question.data_type === 'boolean') {
            this.questionAnswers[question.id] = null
          } else {
            this.questionAnswers[question.id] = ''
          }
        })
      }
      this.dialogAnswerQuestions = true
    },
    closeAnswerDialog() {
      this.dialogAnswerQuestions = false
      this.currentGroup = null
      this.questionAnswers = {}
    },
    async saveAnswers() {
      try {
        const answersToSave = []
        for (const [questionId, answer] of Object.entries(this.questionAnswers)) {
          if (answer === null || answer === '') continue
          answersToSave.push({
            perspective: parseInt(questionId),
            project: parseInt(this.projectId),
            answer: String(answer)
          })
        }
        if (answersToSave.length === 0) {
          this.snackbarErrorMessage = 'Please answer at least one question'
          this.snackbarError = true
          return
        }
        const savePromises = answersToSave.map(answer =>
          this.$services.perspective.createPerspectiveAnswer(this.projectId, answer)
        )
        await Promise.all(savePromises)
        this.snackbarMessage = 'Answers submitted successfully!'
        this.snackbar = true
        this.closeAnswerDialog()
      } catch (e) {
        console.error('Error saving answers:', e)
        if (!e.response) {
          this.snackbarErrorMessage = 'De momento não é possivel realizar esta operação.'
        } else if (e.response.status >= 500) {
          this.snackbarErrorMessage = 'De momento não é possivel realizar esta operação.'
        } else {
          this.snackbarErrorMessage = e.response.data?.detail || 'Error saving answers'
        }
        this.snackbarError = true
      }
    },

    // ---------------------------------------------------------------------
    // DETALHES & ELIMINAR PERGUNTA
    // ---------------------------------------------------------------------
    showQuestionDetails(question) {
      console.log('Question details:', question)
      // Podes abrir um modal adicional, se quiseres
    },
    confirmDeleteQuestion(question) {
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
        this.fetchPerspectiveGroups()
      } catch (e) {
        console.error('Error deleting question:', e)
        if (!e.response) {
          this.snackbarErrorMessage = 'De momento não é possivel realizar esta operação.'
        } else if (e.response.status >= 500) {
          this.snackbarErrorMessage = 'De momento não é possivel realizar esta operação.'
        } else {
          this.snackbarErrorMessage = e.response.data?.detail || 'Error deleting question'
        }
        this.snackbarError = true
      }
    },

    // ---------------------------------------------------------------------
    // FUNÇÕES AUXILIARES (OPÇÕES)
    // ---------------------------------------------------------------------
    addOption() {
      this.editedQuestion.options.push('')
    },
    removeOption(index) {
      this.editedQuestion.options.splice(index, 1)
    }
  }
}
</script>

<style scoped>
::v-deep .v-dialog {
  width: 500px;
}
</style>
