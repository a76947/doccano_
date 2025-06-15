<template>
  <v-card>
    <v-card-title>
      <v-btn 
        v-if="!hasGroups"
        class="text-capitalize" 
        color="primary" 
        @click.stop="openCreateGroupDialog()"
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

    <!-- >>> COLE AQUI: início do Create Group Modal <<< -->
    <v-dialog v-model="dialogCreateGroup" max-width="500px">
      <v-card>
        <v-card-title class="headline">Create Perspective Group</v-card-title>
        <v-card-text>
          <!-- campos do grupo -->
          <v-text-field
            v-model="editedGroup.name"
            label="Group Name *"
            :rules="[v => !!v || 'Group name is required']"
            required
            :error-messages="groupFormErrors.name ? 'Group name is required' : ''"
          />
          <v-textarea
            v-model="editedGroup.description"
            label="Description"
            rows="3"
          />

          <v-divider class="my-4" />

          <!-- Questão Inicial -->
          <h3 class="subtitle-1 mb-2">Questão Inicial (obrigatória)</h3>
          <v-text-field
            v-model="newGroupQuestion.question"
            label="Texto da Questão *"
            :rules="[v => !!v || 'Question text is required']"
            required
            :error-messages="groupFormErrors.question ? 'Question text is required' : ''"
          />
          <v-select
            v-model="newGroupQuestion.data_type"
            :items="dataTypes"
            label="Tipo de Dado *"
            :rules="[v => !!v || 'Data type is required']"
            required
            :error-messages="groupFormErrors.data_type ? 'Data type is required' : ''"
          />
          <div v-if="newGroupQuestion.data_type==='string' || newGroupQuestion.data_type==='int'">
            <v-btn small color="primary" @click="newGroupQuestion.options.push('')">
              <v-icon small left>mdi-plus</v-icon>Add Option
            </v-btn>
            <div v-if="groupFormErrors.options" class="error--text caption mt-1">
              At least two options are required
            </div>
            <v-text-field
              v-for="(opt,i) in newGroupQuestion.options"
              :key="i"
              v-model="newGroupQuestion.options[i]"
              :label="`Option ${i+1} *`"
              :rules="[v => !!v || 'Option is required']"
              required
              :error-messages="groupFormErrors.options ? 'Option is required' : ''"
              class="mt-2"
            />
          </div>
        </v-card-text>
        <v-card-actions>
          <v-spacer/>
          <v-btn text @click="closeGroupDialog">Cancel</v-btn>
          <v-btn color="primary" text @click="validateAndSaveGroup">Save</v-btn>
        </v-card-actions>
      </v-card>
    </v-dialog>

    <!-- Create Group Modal (igual ao que já tens) -->
    <!-- … aqui vai o teu <v-dialog v-model="dialogCreateGroup"> … </v-dialog> … -->

    <!-- Lista de Grupos -->
    <v-expansion-panels v-if="hasGroups" v-model="expandedPanel">
      <v-expansion-panel v-for="group in perspectiveGroups" :key="group.id">
        <v-expansion-panel-header>
          {{ group.name }}
          <v-spacer/>
          <v-btn small color="primary" @click.stop="openAddQuestionDialog(group)">
            <v-icon left small>mdi-plus</v-icon>
            Add Question
          </v-btn>
          <v-btn 
            :disabled="!group.questions.length"
            small 
            color="success" 
            @click.stop="openAnswerDialog(group)"
          >
            <v-icon left small>mdi-text-box-check-outline</v-icon>
            Answer
          </v-btn>
          <v-btn
            small
            color="error"
            class="ml-2"
            :disabled="groupHasResponses"
            @click.stop="openDeleteGroupDialog(group)"
          >
            <v-icon left small>mdi-delete</v-icon>
            Delete Group
          </v-btn>
        </v-expansion-panel-header>
        <v-expansion-panel-content>
          <div v-if="group.questions.length">
            <v-simple-table>
              <thead>
                <tr>
                  <th>Question</th>
                  <th>Type</th>
                  <th class="text-right">Actions</th>
                </tr>
              </thead>
              <tbody>
                <tr v-for="q in group.questions" :key="q.id">
                  <td>{{ q.question }}</td>
                  <td>{{ q.data_type }}</td>
                  <td class="text-right">
                    <v-btn
                      small
                      color="info"
                      class="mr-2"
                      @click="showQuestionResponses(q)"
                    >
                      <v-icon small left>mdi-eye</v-icon>
                      View Responses
                    </v-btn>
                    <v-btn
                      small
                      color="primary"
                      class="mr-2"
                      @click="openEditQuestionDialog(group, q)"
                    >
                      <v-icon small left>mdi-pencil</v-icon>
                      Edit
                    </v-btn>
                    <v-btn
                      small
                      color="error"
                      @click="openDeleteQuestionDialog(group, q)"
                    >
                      <v-icon small left>mdi-delete</v-icon>
                      Delete
                    </v-btn>
                  </td>
                </tr>
              </tbody>
            </v-simple-table>
          </div>
          <div v-else class="text-center pa-3">
            No questions yet.
          </div>
        </v-expansion-panel-content>
      </v-expansion-panel>
    </v-expansion-panels>
 
    <!-- Add Question Dialog -->
    <v-dialog 
      v-model="dialogAddQuestion" 
      max-width="500px" 
      :persistent="currentGroup?.questions?.length === 0"
      :hide-overlay="currentGroup?.questions?.length === 0"
      :no-click-animation="currentGroup?.questions?.length === 0"
    >
      <v-card>
        <v-card-title class="headline">
          {{ currentGroup?.questions?.length === 0 ? 'Add First Question (Required)' : 
          'Add Question' }}
        </v-card-title>
        <v-card-text>
          <!-- Campo pergunta obrigatório -->
          <v-text-field
            v-model="newQuestion.question"
            label="Question Text *"
            :rules="[v => !!v || 'Question text is required']"
            required
            :error-messages="questionFormErrors.question ? 'Question text is required' : ''"
          />

          <!-- Campo data_type obrigatório -->
          <v-select
            v-model="newQuestion.data_type"
            :items="dataTypes"
            label="Data Type *"
            :rules="[v => !!v || 'Data type is required']"
            required
            :error-messages="questionFormErrors.data_type ? 'Data type is required' : ''"
            @change="clearOptions"
          />

          <!-- Opções (string/int) também com regra -->
          <div
            v-if="newQuestion.data_type === 'string' ||
                  newQuestion.data_type === 'int'"
          >
            <v-btn
              small
              color="primary"
              @click="newQuestion.options.push('')"
            >
              <v-icon small left>mdi-plus</v-icon>
              Add Option
            </v-btn>
            <div v-if="questionFormErrors.options" class="error--text caption mt-1">
              At least two options are required
            </div>
            <v-text-field
              v-for="(opt, i) in newQuestion.options"
              :key="i"
              v-model="newQuestion.options[i]"
              :label="`Option ${i+1} *`"
              :rules="[
                v => !!v || 'Option is required',
                v => validateOptionType(v, newQuestion.data_type) || 
                     (newQuestion.data_type === 'int' ? 'Must be a number' : 'Must be text')
              ]"
              required
              :error-messages="questionFormErrors.options ? 'Option is required' : ''"
              class="mt-2"
              :type="newQuestion.data_type === 'int' ? 'number' : 'text'"
              @input="validateOption(i)"
              @keypress="newQuestion.data_type === 'int' ? onlyNumbers($event) : null"
              @paste="newQuestion.data_type === 'int' ? preventPaste($event) : null"
            />
          </div>
        </v-card-text>
        <v-card-actions>
          <v-spacer />
          <v-btn 
            v-if="currentGroup?.questions?.length > 0"
            text 
            @click="dialogAddQuestion = false"
          >
            Cancel
          </v-btn>
          <v-btn
            color="primary"
            text
            @click="validateAndSaveQuestion"
          >
            Save
          </v-btn>
        </v-card-actions>
      </v-card>
    </v-dialog>
     
    

   

   

   

    <!-- Answer Questions Dialog -->
    <v-dialog v-model="dialogAnswer" max-width="600px">
      <v-card>
        <v-card-title class="headline">Answer Questions for {{ currentGroup?.name }}</v-card-title>
        <v-card-text>
          <div v-for="q in currentGroup?.questions" :key="q.id" class="mb-4">
            <h3>{{ q.question }}</h3>
            <v-radio-group v-model="answers[q.id]" row>
              <v-radio
                v-for="opt in (q.data_type === 'boolean' ? ['Yes','No'] : q.options)"
                :key="opt"
                :label="opt"
                :value="opt"
              />
            </v-radio-group>
          </div>
        </v-card-text>
        <v-card-actions>
          <v-spacer/>
          <v-btn text @click="dialogAnswer = false">Cancel</v-btn>
          <v-btn color="success" text @click="saveAnswers">Submit</v-btn>
        </v-card-actions>
      </v-card>
    </v-dialog>

    <!-- Select Example Dialog -->
    <v-dialog v-model="dialogSelectExample" max-width="500px">
      <v-card>
        <v-card-title class="headline">Select an Example</v-card-title>
        <v-card-text>
          <p class="mb-4">Please select an example to answer the questions for:</p>
          <v-list>
            <v-list-item
              v-for="example in examples"
              :key="example.id"
              @click="selectExampleAndContinue(example)"
            >
              <v-list-item-content>
                <v-list-item-title>{{ example.text || `Example ${example.id}` }}</v-list-item-title>
                <v-list-item-subtitle v-if="example.metadata">
                  {{ example.metadata.description || '' }}
                </v-list-item-subtitle>
              </v-list-item-content>
            </v-list-item>
          </v-list>
        </v-card-text>
        <v-card-actions>
          <v-spacer/>
          <v-btn text @click="dialogSelectExample = false">Cancel</v-btn>
        </v-card-actions>
      </v-card>
    </v-dialog>

    <!-- Edit Question Dialog -->
    <v-dialog v-model="dialogEditQuestion" max-width="500px">
      <v-card>
        <v-card-title class="headline">
          Edit Question
        </v-card-title>
        <v-card-text>
          <v-text-field
            v-model="editingQuestion.question"
            label="Question Text *"
            :rules="[v => !!v || 'Question text is required']"
            required
            :error-messages="editFormErrors.question ? 'Question text is required' : ''"
          />

          <v-select
            v-model="editingQuestion.data_type"
            :items="dataTypes"
            label="Data Type *"
            :rules="[v => !!v || 'Data type is required']"
            required
            :error-messages="editFormErrors.data_type ? 'Data type is required' : ''"
          />

          <div
            v-if="editingQuestion.data_type === 'string' ||
                  editingQuestion.data_type === 'int'"
          >
            <v-btn
              small
              color="primary"
              @click="editingQuestion.options.push('')"
            >
              <v-icon small left>mdi-plus</v-icon>
              Add Option
            </v-btn>
            <div v-if="editFormErrors.options" class="error--text caption mt-1">
              At least two options are required
            </div>
            <v-text-field
              v-for="(opt, i) in editingQuestion.options"
              :key="i"
              v-model="editingQuestion.options[i]"
              :label="`Option ${i+1} *`"
              :rules="[v => !!v || 'Option is required']"
              required
              :error-messages="editFormErrors.options ? 'Option is required' : ''"
              class="mt-2"
            />
          </div>
        </v-card-text>
        <v-card-actions>
          <v-spacer />
          <v-btn text @click="dialogEditQuestion = false">
            Cancel
          </v-btn>
          <v-btn
            color="primary"
            text
            @click="validateAndSaveEdit"
          >
            Save
          </v-btn>
        </v-card-actions>
      </v-card>
    </v-dialog>

    <!-- View Responses Dialog -->
    <v-dialog v-model="dialogViewResponses" max-width="800px">
      <v-card>
        <v-card-title class="headline">
          Responses for: {{ viewingQuestion?.question }}
        </v-card-title>
        <v-card-text>
          <v-data-table
            :headers="responseHeaders"
            :items="questionResponses"
            :loading="loadingResponses"
            class="elevation-1"
          >
            <template #[`item.answer`]="{ item }">
              {{ item.answer }}
            </template>
            <template #[`item.created_at`]="{ item }">
              {{ new Date(item.created_at).toLocaleString() }}
            </template>
          </v-data-table>

          <!-- Vote Count Summary -->
          <v-card class="mt-4" flat>
            <v-card-title>Vote Summary</v-card-title>
            <v-card-text>
              <v-list>
                <v-list-item v-for="(count, answer) in voteCounts" :key="answer">
                  <v-list-item-content>
                    <v-list-item-title>{{ answer }}</v-list-item-title>
                    <v-list-item-subtitle>
                      Votes: {{ count }} ({{ calculatePercentage(count) }}%)
                    </v-list-item-subtitle>
                  </v-list-item-content>
                </v-list-item>
              </v-list>
            </v-card-text>
          </v-card>
        </v-card-text>
        <v-card-actions>
          <v-spacer />
          <v-btn text @click="dialogViewResponses = false">Close</v-btn>
        </v-card-actions>
      </v-card>
    </v-dialog>

    <!-- Delete Group Dialog -->
    <v-dialog v-model="dialogDeleteGroup" max-width="400px">
      <v-card>
        <v-card-title class="headline">Delete Perspective Group</v-card-title>
        <v-card-text>
          <div v-if="groupHasResponses" 
            class="red--text text--darken-1 font-weight-bold">
            Cannot delete group because it has responses.
            Please delete all responses first.
          </div>
          <template v-else>
            Are you sure you want to delete the perspective group:
            <div class="mt-2 font-weight-bold">{{ deletingGroup?.name }}</div>
            <div class="red--text text--darken-1 font-weight-bold">This action cannot be 
              undone and will delete all associated questions!</div>
          </template>
        </v-card-text>
        <v-card-actions>
          <v-spacer />
          <v-btn text @click="dialogDeleteGroup = false">
            Cancel
          </v-btn>
          <v-btn
            color="error"
            text
            :disabled="groupHasResponses"
            @click="deleteGroup"
          >
            Delete
          </v-btn>
        </v-card-actions>
      </v-card>
    </v-dialog>

    <!-- Delete Question Dialog -->
    <v-dialog v-model="dialogDeleteQuestion" max-width="400px">
      <v-card>
        <v-card-title class="headline">Delete Question</v-card-title>
        <v-card-text>
          Are you sure you want to delete the question:
          <div class="mt-2 font-weight-bold">{{ deletingQuestion?.question }}</div>
          <div class="red--text text--darken-1 font-weight-bold">This action cannot be 
            undone and will delete all associated answers!</div>
        </v-card-text>
        <v-card-actions>
          <v-spacer />
          <v-btn text @click="dialogDeleteQuestion = false">
            Cancel
          </v-btn>
          <v-btn
            color="error"
            text
            @click="deleteQuestion"
          >
            Delete
          </v-btn>
        </v-card-actions>
      </v-card>
    </v-dialog>

    <!-- Snackbars -->
    <v-snackbar v-model="snackbar" top color="success">
      {{ snackbarMessage }}
      <v-btn text @click="snackbar = false">Close</v-btn>
    </v-snackbar>
    <v-snackbar v-model="snackbarError" top color="error">
      {{ snackbarErrorMessage }}
      <v-btn text @click="snackbarError = false">Close</v-btn>
    </v-snackbar>
  </v-card>
</template>

<script>
import { usePerspectiveApplicationService } from '@/services/application/perspective/perspectiveApplicationService'

export default {
  layout: 'project',
  middleware: ['check-auth', 'auth', 'setCurrentProject'],

  validate({ params }) {
    return /^\d+$/.test(params.id)
  },

  data() {
    return {
      // Create‐group
      dialogCreateGroup: false,
      editedGroup: { name:'', description:'' },
      newGroupQuestion: { question:'', data_type:'string', options:[] },
      groupFormErrors: {
        name: false,
        question: false,
        data_type: false,
        options: false
      },

      // Listagem
      perspectiveGroups: [],
      expandedPanel: null,
      currentGroup: null,

      // Add Question
      dialogAddQuestion: false,
      questionFormErrors: {
        question: false,
        data_type: false,
        options: false
      },

      // Edit Question
      dialogEditQuestion: false,
      editingQuestion: { question:'', data_type:'string', options:[] },
      editFormErrors: {
        question: false,
        data_type: false,
        options: false
      },

      // Answer
      dialogAnswer: false,
      newQuestion: { question:'', data_type:'string', options:[] },
      answers: {},

      // Data Types
      dataTypes: [
        { text: 'Text (options)', value: 'string' },
        { text: 'Number (options)', value: 'int' },
        { text: 'Yes/No', value: 'boolean' }
      ],

      // Snackbars
      snackbar: false,
      snackbarMessage: '',
      snackbarError: false,
      snackbarErrorMessage: '',
      showErrors: false,
      questionAnswers: {},

      // View Responses
      dialogViewResponses: false,
      viewingQuestion: null,
      questionResponses: [],
      loadingResponses: false,

      responseHeaders: [
        { text: 'Answer', value: 'answer' },
        { text: 'Submitted At', value: 'created_at' }
      ],
      voteCounts: {},

      knownUsers: [],


      // Delete Group
      dialogDeleteGroup: false,
      deletingGroup: null,
      groupHasResponses: false,

      // Delete Question
      dialogDeleteQuestion: false,
      deletingQuestion: null,
      deletingQuestionGroup: null,

      examples: [],
      selectedExample: null,
      dialogSelectExample: false

    }
  },

  computed: {
    projectId() {
      return this.$route.params.id
    },
    hasGroups() {
      return this.perspectiveGroups.length > 0
    },
    
    validGroups() {
      return this.perspectiveGroups.filter(group => !!group)
    },

    isAdmin() {
      const currentProject = this.$store.getters['projects/currentProject']
      return currentProject?.role === 'admin' || currentProject?.role === 'project_admin'
    },

    responseStats() {
      return {};
    }
  },

  mounted() {
    this.fetchPerspectiveGroups()
  },

  methods: {
    async fetchPerspectiveGroups() {
      try {
        const res = await this.$services.perspective.listPerspectiveGroups(this.projectId)
        this.perspectiveGroups = res.results || res.data?.results || []
      } catch (e) {
        console.error('Erro fetching groups', e)
        this.snackbarErrorMessage = 'Erro ao carregar grupos'
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

    closeGroupDialog() {
      this.dialogCreateGroup = false
      this.editedGroup = { name:'', description:'' }
      this.newGroupQuestion = { question:'', data_type:'string', options:[] }
      this.groupFormErrors = {
        name: false,
        question: false,
        data_type: false,
        options: false
      }
    },

    async validateAndSaveGroup() {
      const g = this.editedGroup;
      const q = this.newGroupQuestion;
      
      this.groupFormErrors = {
        name: !g.name,
        question: !q.question,
        data_type: !q.data_type,
        options: (q.data_type === 'string' || q.data_type === 'int') && q.options.length < 2
      };

      if (Object.values(this.groupFormErrors).some(Boolean)) {
        return;
      }

      try {
        const { id: groupId } = 
        await this.$services.perspective.createPerspectiveGroup(this.projectId, {
          ...g,
          initial_question: {
            question: q.question,
            data_type: q.data_type,
            options: q.options.filter(o => o.trim())
          }
        });
        
        this.snackbarMessage = 'Group and question created successfully!';
        this.snackbar = true;
        this.closeGroupDialog();
        await this.fetchPerspectiveGroups();
        this.expandedPanel = this.perspectiveGroups.findIndex(gr => gr.id === groupId);
      } catch (err) {
        console.error(err);
        this.snackbarErrorMessage = err.response?.data?.detail || 'Error creating group';
        this.snackbarError = true;
      }
    },

    async saveGroup() {
      await this.validateAndSaveGroup();
    },

    openAddQuestionDialog(group) {
      this.currentGroup = group
      this.newQuestion = { question:'', data_type:'string', options:[] }
      this.questionFormErrors = {
        question: false,
        data_type: false,
        options: false
      }
      this.dialogAddQuestion = true
    },

    onlyNumbers(event) {
      const keyCode = event.keyCode || event.which;
      const keyValue = String.fromCharCode(keyCode);
      // Permite apenas números e teclas de controle (backspace, delete, etc)
      if (!/^\d$/.test(keyValue) && 
          keyCode !== 8 && // backspace
          keyCode !== 46 && // delete
          keyCode !== 37 && // left arrow
          keyCode !== 39) { // right arrow
        event.preventDefault();
      }
    },

    preventPaste(event) {
      if (this.newQuestion.data_type === 'int') {
        event.preventDefault();
        const pastedText = (event.clipboardData || window.clipboardData).getData('text');
        if (!/^\d+$/.test(pastedText)) {
          this.snackbarErrorMessage = 'Only numbers are allowed';
          this.snackbarError = true;
        } else {
          this.newQuestion.options[event.target.dataset.index] = pastedText;
        }
      }
    },

    validateOptionType(value, type) {
      if (!value) return true;
      if (type === 'int') {
        return /^\d+$/.test(value) && Number.isInteger(Number(value));
      }
      return true; // Para string, aceita qualquer texto
    },

    validateOption(index) {
      const value = this.newQuestion.options[index];
      if (this.newQuestion.data_type === 'int') {
        // Remove qualquer caractere não numérico
        this.newQuestion.options[index] = value.replace(/\D/g, '');
      }
    },

    async validateAndSaveQuestion() {
      const q = this.newQuestion;
      this.questionFormErrors = {
        question: !q.question,
        data_type: !q.data_type,
        options: (q.data_type === 'string' || q.data_type === 'int') && q.options.length < 2
      };

      if (Object.values(this.questionFormErrors).some(Boolean)) {
        return;
      }

      try {
        const payload = {
          project: this.projectId,
          group: this.currentGroup.id,
          name: q.question,
          question: q.question,
          data_type: q.data_type,
          options: q.options.filter(o => o.trim())
        };

        await this.$services.perspective.createPerspective(this.projectId, payload);
        this.dialogAddQuestion = false;
        await this.fetchPerspectiveGroups();
        this.snackbarMessage = 'Question added successfully';
        this.snackbar = true;
      } catch (e) {
        console.error(e);
        this.snackbarErrorMessage = e.response?.data?.detail || 'Error adding question';
        this.snackbarError = true;
      }
    },

    async saveQuestion() {
      await this.validateAndSaveQuestion();
    },

    openAnswerDialog(group) {
      this.currentGroup = group
      this.answers = {}
      
      // Inicializa as respostas para cada pergunta
      this.currentGroup.questions.forEach(q => {
        this.answers[q.id] = null
      })
      
      // Abre diretamente o diálogo de respostas
      this.dialogAnswer = true
    },

    selectExampleAndContinue(example) {
      this.selectedExample = example
      this.dialogSelectExample = false
      
      // Inicializa as respostas para cada pergunta
      this.currentGroup.questions.forEach(q => {
        this.answers[q.id] = null
      })
      
      this.dialogAnswer = true
    },

    async saveAnswers() {
      try {
        const answersToSave = []
        
        console.log('Starting saveAnswers process...')
        console.log('Current answers:', this.answers)
        console.log('Current project ID:', this.projectId)
        
        // Se não houver exemplo selecionado, tentamos obter o exemplo atual
        if (!this.selectedExample) {
          try {
            console.log('Attempting to get current example...')
            this.selectedExample = await this.$services.example.getCurrentExample(this.projectId)
            console.log('Current example response:', this.selectedExample)
          } catch (error) {
            console.error('Error getting current example:', error)
            // Continua mesmo sem exemplo, pois não é obrigatório
          }
        }
        
        for (const [questionId, answer] of Object.entries(this.answers)) {
          if (answer === null || answer === '') {
            console.log('Skipping empty answer for question:', questionId)
            continue
          }
          
          const answerData = {
            perspective: parseInt(questionId),
            project: parseInt(this.projectId),
            answer: String(answer)
          }

          // Adiciona o exemplo apenas se estiver disponível
          if (this.selectedExample && this.selectedExample.id) {
            answerData.example = this.selectedExample.id
          }
          
          console.log('Preparing answer data:', answerData)
          answersToSave.push(answerData)
        }
        
        if (answersToSave.length === 0) {
          console.error('No valid answers to save')
          this.snackbarErrorMessage = 'Please answer at least one question'
          this.snackbarError = true
          return
        }
        
        console.log('Attempting to save answers:', answersToSave)
        
        const service = usePerspectiveApplicationService()
        for (const answer of answersToSave) {
          try {
            console.log('Submitting answer:', answer)
            const response = await service.createPerspectiveAnswer(this.projectId, answer)
            console.log('Answer submission response:', response)
          } catch (answerError) {
            console.error('Error submitting individual answer:', answerError)
            console.error('Error details:', {
              message: answerError.message,
              response: answerError.response?.data,
              status: answerError.response?.status
            })
            throw answerError
          }
        }
        
        this.snackbarMessage = 'Answers submitted successfully!'
        this.snackbar = true
        this.dialogAnswer = false
        this.answers = {} // Clear answers after successful submission
        this.selectedExample = null // Clear selected example
      } catch (e) {
        console.error('Error saving answers:', e)
        console.error('Error details:', {
          message: e.message,
          response: e.response?.data,
          status: e.response?.status
        })
        this.snackbarErrorMessage = e.response?.data?.detail || e.message || 'Error saving answers'
        this.snackbarError = true
      }
    },

    calculateVoteCounts(responses) {
      const counts = {}
      responses.forEach(response => {
        const answer = response.answer
        counts[answer] = (counts[answer] || 0) + 1
      })
      return counts
    },

    calculatePercentage(count) {
      const total = Object.values(this.voteCounts).reduce((a, b) => a + b, 0)
      return total > 0 ? Math.round((count / total) * 100) : 0
    },

    async showQuestionResponses(question) {
      this.viewingQuestion = question;
      this.loadingResponses = true;
      this.dialogViewResponses = true;
      
      try {
        const service = usePerspectiveApplicationService()
        const response = await service.listPerspectiveAnswersByQuestion(
          this.projectId,
          question.id
        );
        this.questionResponses = response.results || [];
        this.voteCounts = this.calculateVoteCounts(this.questionResponses);
      } catch (error) {
        console.error('Error fetching responses:', error);
        this.snackbarErrorMessage = 'Failed to fetch responses';
        this.snackbarError = true;
      } finally {
        this.loadingResponses = false;
      }
    },

    openEditQuestionDialog(_group, question) {
      this.currentGroup = _group
      this.editingQuestion = { ...question }
      this.editFormErrors = {
        question: false,
        data_type: false,
        options: false
      }
      this.dialogEditQuestion = true
    },

    async validateAndSaveEdit() {
      const q = this.editingQuestion
      this.editFormErrors = {
        question: !q.question,
        data_type: !q.data_type,
        options: (q.data_type === 'string' || q.data_type === 'int') && q.options.length < 2
      }

      if (Object.values(this.editFormErrors).some(Boolean)) {
        return
      }

      try {
        await this.$services.perspective.updatePerspective(
          this.projectId,
          q.id,
          {
            project: this.projectId,
            group: this.currentGroup.id,
            name: q.question,
            question: q.question,
            data_type: q.data_type,
            options: q.options.filter(o => o.trim())
          }
        )
        this.dialogEditQuestion = false
        await this.fetchPerspectiveGroups()
        this.snackbarMessage = 'Question updated successfully'
        this.snackbar = true
      } catch (e) {
        console.error(e)
        this.snackbarErrorMessage = e.response?.data?.detail || 'Error updating question'
        this.snackbarError = true
      }
    },

    clearOptions() {
      // Limpa as opções quando muda o tipo
      this.newQuestion.options = [];
    },

    async fetchBasicUserInfo() {
      try {
        // Try to get members list if user is admin
        const response = await this.$axios.get(`/v1/projects/${this.projectId}/members`);
        if (response.data) {
          this.knownUsers = response.data.map(member => ({
            id: member.user,
            username: member.username || `User ${member.user}`
          }));
        }
      } catch (error) {
        // If forbidden (normal user), create basic user list from available data
        console.log("Unable to fetch member list, using basic user info");
        
        // Create entries for users we know about
        this.knownUsers = [
          // Current user
          { 
            id: this.$store.getters.getUserId, 
            username: this.$store.getters.getUsername || `User ${this.$store.getters.getUserId}`
          }
        ];
        
        // Add comparison users if they're different from current user
        if (this.comparisonUsers) {
          if (this.comparisonUsers.user1 && 
              this.comparisonUsers.user1 !== this.$store.getters.getUserId) {
            this.knownUsers.push({
              id: this.comparisonUsers.user1,
              username: `User ${this.comparisonUsers.user1}`
            });
          }
          
          if (this.comparisonUsers.user2 && 
              this.comparisonUsers.user2 !== this.$store.getters.getUserId) {
            this.knownUsers.push({
              id: this.comparisonUsers.user2,
              username: `User ${this.comparisonUsers.user2}`
            });
          }
        }
      }
    },

    // Update the openComparisonDialog method to fetch user info
    async openComparisonDialog(params) {
      this.selectedDocumentId = params.documentId;
      this.comparisonUsers = {
        user1: params.user1 || this.$store.getters.getUserId,
        user2: params.user2
      };
      
      // Try to fetch user info before showing the dialog
      await this.fetchBasicUserInfo();
      
      // Now show the dialog
      this.dialogCompare = true;
    },

    async hasGroupResponses(group) {
      if (!group) return false;
      
      try {
        // Check each question in the group for responses
        for (const question of group.questions) {
          const service = usePerspectiveApplicationService();
          const response = await service.listPerspectiveAnswersByQuestion(
            this.projectId,
            question.id
          );
          if (response.results && response.results.length > 0) {
            return true;
          }
        }
        return false;
      } catch (error) {
        console.error('Error checking group responses:', error);
        return true; // If there's an error, assume there are responses to be safe
      }
    },

    async openDeleteGroupDialog(group) {
      this.deletingGroup = group;
      this.groupHasResponses = await this.hasGroupResponses(group);
      
      if (this.groupHasResponses) {
        this.snackbarErrorMessage = 'Cannot delete group because it has responses. Please delete all responses first.';
        this.snackbarError = true;
        return;
      }
      
      this.dialogDeleteGroup = true;
    },

    async deleteGroup() {
      if (!this.deletingGroup) return;

      // Double check if group has responses before deleting
      const hasResponses = await this.hasGroupResponses(this.deletingGroup);
      if (hasResponses) {
        this.snackbarErrorMessage = 'Cannot delete group because it has responses. Please delete all responses first.';
        this.snackbarError = true;
        this.dialogDeleteGroup = false;
        return;
      }

      try {
        const service = usePerspectiveApplicationService();
        await service.deletePerspectiveGroup(
          this.projectId,
          this.deletingGroup.id
        );
        this.dialogDeleteGroup = false;
        await this.fetchPerspectiveGroups();
        this.snackbarMessage = 'Perspective group deleted successfully';
        this.snackbar = true;
      } catch (e) {
        console.error('Error deleting group:', e);
        console.error('Error details:', {
          message: e.message,
          response: e.response?.data,
          status: e.response?.status
        });
        this.snackbarErrorMessage = e.response?.data?.detail || e.message || 'Error deleting perspective group';
        this.snackbarError = true;
      }
    },

    openDeleteQuestionDialog(group, question) {
      this.deletingQuestion = question;
      this.deletingQuestionGroup = group;
      this.dialogDeleteQuestion = true;
    },

    async deleteQuestion() {
      if (!this.deletingQuestion) return;

      try {
        await this.$services.perspective.deletePerspective(
          this.projectId,
          this.deletingQuestion.id
        );
        this.dialogDeleteQuestion = false;
        await this.fetchPerspectiveGroups();
        this.snackbarMessage = 'Question deleted successfully';
        this.snackbar = true;
      } catch (e) {
        console.error(e);
        this.snackbarErrorMessage = e.response?.data?.detail || 'Error deleting question';
        this.snackbarError = true;
      }
    },
  }
}
</script>

<style scoped>
/* os teus estilos continuam aqui */
</style>