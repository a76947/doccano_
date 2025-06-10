<template>
  <v-card>
    <v-card-title>
      <v-btn
        v-if="!hasGroups"
        class="text-capitalize"
        color="primary"
        @click.stop="openCreateGroupDialog"
      >
        Create Perspective Group
      </v-btn>
      <v-alert v-else type="info" dense class="mb-0">
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
          <v-btn small color="success" 
          @click.stop="openAnswerDialog(group)" :disabled="!group.questions.length">
            <v-icon left small>mdi-text-box-check-outline</v-icon>
            Answer
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
 
      <v-dialog v-model="dialogAddQuestion" max-width="500px">
  <v-card>
    <v-card-title class="headline">
      Add Question to {{ currentGroup?.name }}
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
          :rules="[v => !!v || 'Option is required']"
          required
          :error-messages="questionFormErrors.options ? 'Option is required' : ''"
          class="mt-2"
        />
      </div>
    </v-card-text>
    <v-card-actions>
      <v-spacer />
      <v-btn text @click="dialogAddQuestion = false">
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

    <!-- Delete Question Dialog -->
    <v-dialog v-model="dialogDeleteQuestion" max-width="400px">
      <v-card>
        <v-card-title class="headline">Delete Question</v-card-title>
        <v-card-text>
          Are you sure you want to delete this question?
          <div class="mt-2 font-weight-bold">{{ deletingQuestion?.question }}</div>
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
export default {
  layout: 'project',
  middleware: ['check-auth','auth','setCurrentProject'],

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

      // Add Question
      dialogAddQuestion: false,
      questionFormErrors: {
        question: false,
        data_type: false,
        options: false
      },

      // Answer
      dialogAnswer: false,
      currentGroup: null,
      newQuestion: { question:'', data_type:'string', options:[] },
      answers: {},

       // **Data Types para o v-select**
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

      // Edit Question
      dialogEditQuestion: false,
      editingQuestion: { question: '', data_type: 'string', options: [] },
      editFormErrors: {
        question: false,
        data_type: false,
        options: false
      },

      // Delete Question
      dialogDeleteQuestion: false,
      deletingQuestion: null,
    }
  },

  computed: {
    projectId() {
      return this.$route.params.id
    },
    hasGroups() {
      return this.perspectiveGroups.length > 0
    },
    isGroupFormValid() {
      const g = this.editedGroup;
      const q = this.newGroupQuestion;
      
      if (!g.name || !q.question || !q.data_type) return false;
      
      if ((q.data_type === 'string' || q.data_type === 'int') && 
          (!q.options.length || q.options.some(o => !o.trim()))) {
        return false;
      }
      
      return true;
    },
    isQuestionFormValid() {
      const q = this.newQuestion;
      
      if (!q.question || !q.data_type) return false;
      
      if ((q.data_type === 'string' || q.data_type === 'int') && 
          (!q.options.length || q.options.some(o => !o.trim()))) {
        return false;
      }
      
      return true;
    }
  },

  mounted() {
    this.fetchPerspectiveGroups()
  },

  methods: {
    // 1) BUSCAR GRUPOS+QUESTÕES
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

    // 2) CREATE GROUP + QUESTÃO INICIAL
    openCreateGroupDialog() { this.dialogCreateGroup = !this.hasGroups },
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
    async saveGroup() {
      const g = this.editedGroup
      const q = this.newGroupQuestion
      if (!g.name||!q.question||!q.data_type) return
      if ((q.data_type==='string'||q.data_type==='int') && !q.options.length) return

      try {
        const { id: groupId } =
         await this.$services.perspective.createPerspectiveGroup(this.projectId, {
           ...g,
           initial_question: {
             question: q.question,
             data_type: q.data_type,
             options: q.options.filter(o=>o.trim())
           }
         })
        this.snackbarMessage='Grupo e questão criados!'
        this.snackbar=true
        this.closeGroupDialog()
        await this.fetchPerspectiveGroups()
        this.expandedPanel = this.perspectiveGroups.findIndex(gr=>gr.id===groupId)
      } catch(err) {
        console.error(err)
        this.snackbarErrorMessage = err.response?.data?.detail || 'Erro ao criar grupo'
        this.snackbarError = true
      }
    },

    // 3) ADD QUESTION
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
    async saveQuestion() {
      const q = this.newQuestion;
      if (!q.question || !q.data_type) return;

      const payload = {
        project: this.projectId,
        group: this.currentGroup.id,
        name: q.question,
        question: q.question,
        data_type: q.data_type,
        options: q.options.filter(o => o.trim())
      };

      try {
        await this.$services.perspective.createPerspective(this.projectId, payload);
        this.dialogAddQuestion = false;
        await this.fetchPerspectiveGroups();
        this.snackbarMessage = 'Question added successfully';
        this.snackbar = true;
      } catch (e) {
        const msg = e.response?.data?.question?.[0] || 'Error adding question';
        this.snackbarErrorMessage = msg;
        this.snackbarError = true;
      }
    },

    // 4) ANSWER QUESTIONS
    openAnswerDialog(group) {
      this.currentGroup = group
      this.answers = {}
      group.questions.forEach(q=>{ this.answers[q.id]=null })
      this.dialogAnswer = true
    },
    async saveAnswers() {
      const payloads = Object.entries(this.answers)
        .filter(([_,ans])=>ans!=null)
        .map(([qid,ans])=>({
          perspective: Number(qid),
          project: this.projectId,
          answer: String(ans)
        }))
      try {
        await Promise.all
        (payloads.map(p=>this.$services.perspective.createPerspectiveAnswer(this.projectId,p)))
        this.dialogAnswer=false
        this.snackbarMessage='Respostas guardadas'
        this.snackbar=true
      } catch(e) {
        console.error(e)
        this.snackbarErrorMessage='Erro ao submeter respostas'
        this.snackbarError=true
      }
    },

    validateAndSaveGroup() {
      // Reset errors
      this.groupFormErrors = {
        name: false,
        question: false,
        data_type: false,
        options: false
      };

      // Validate
      const g = this.editedGroup;
      const q = this.newGroupQuestion;
      
      let hasErrors = false;
      
      if (!g.name) {
        this.groupFormErrors.name = true;
        hasErrors = true;
      }
      
      if (!q.question) {
        this.groupFormErrors.question = true;
        hasErrors = true;
      }
      
      if (!q.data_type) {
        this.groupFormErrors.data_type = true;
        hasErrors = true;
      }
      
      if ((q.data_type === 'string' || q.data_type === 'int')) {
        if (!q.options.length || q.options.length < 2) {
          this.groupFormErrors.options = true;
          hasErrors = true;
        } else if (q.options.some(o => !o.trim())) {
          this.groupFormErrors.options = true;
          hasErrors = true;
        }
      }

      if (!hasErrors) {
        this.saveGroup();
      }
    },

    validateAndSaveQuestion() {
      // Reset errors
      this.questionFormErrors = {
        question: false,
        data_type: false,
        options: false
      };

      // Validate
      const q = this.newQuestion;
      
      let hasErrors = false;
      
      if (!q.question) {
        this.questionFormErrors.question = true;
        hasErrors = true;
      }
      
      if (!q.data_type) {
        this.questionFormErrors.data_type = true;
        hasErrors = true;
      }
      
      if ((q.data_type === 'string' || q.data_type === 'int')) {
        if (!q.options.length || q.options.length < 2) {
          this.questionFormErrors.options = true;
          hasErrors = true;
        } else if (q.options.some(o => !o.trim())) {
          this.questionFormErrors.options = true;
          hasErrors = true;
        }
      }

      if (!hasErrors) {
        this.saveQuestion();
      }
    },

    openEditQuestionDialog(group, question) {
      this.currentGroup = group;
      this.editingQuestion = {
        id: question.id,
        question: question.question,
        data_type: question.data_type,
        options: [...(question.options || [])]
      };
      this.editFormErrors = {
        question: false,
        data_type: false,
        options: false
      };
      this.dialogEditQuestion = true;
    },

    validateAndSaveEdit() {
      // Reset errors
      this.editFormErrors = {
        question: false,
        data_type: false,
        options: false
      };

      // Validate
      const q = this.editingQuestion;
      
      let hasErrors = false;
      
      if (!q.question) {
        this.editFormErrors.question = true;
        hasErrors = true;
      }
      
      if (!q.data_type) {
        this.editFormErrors.data_type = true;
        hasErrors = true;
      }
      
      if ((q.data_type === 'string' || q.data_type === 'int')) {
        if (!q.options.length || q.options.length < 2) {
          this.editFormErrors.options = true;
          hasErrors = true;
        } else if (q.options.some(o => !o.trim())) {
          this.editFormErrors.options = true;
          hasErrors = true;
        }
      }

      if (!hasErrors) {
        this.saveEdit();
      }
    },

    async saveEdit() {
      try {
        const payload = {
          project: Number(this.projectId),
          group: this.currentGroup.id,
          name: this.editingQuestion.question,
          question: this.editingQuestion.question,
          data_type: this.editingQuestion.data_type,
          options: this.editingQuestion.options.filter(o => o.trim())
        };

        await this.$services.perspective.updatePerspective(
          this.projectId,
          this.editingQuestion.id,
          payload
        );

        this.dialogEditQuestion = false;
        await this.fetchPerspectiveGroups();
        this.snackbarMessage = 'Question updated successfully';
        this.snackbar = true;
      } catch (e) {
        console.error(e);
        const errorMessage = e.response?.data?.question?.[0] || e.response?.data?.detail || 'Error updating question';
        this.snackbarErrorMessage = errorMessage;
        this.snackbarError = true;
      }
    },

    openDeleteQuestionDialog(group, question) {
      // Verifica se é a última questão do grupo
      if (group.questions.length <= 1) {
        this.snackbarErrorMessage = 'Cannot delete the last question. A group must have at least one question.';
        this.snackbarError = true;
        return;
      }
      this.currentGroup = group;
      this.deletingQuestion = question;
      this.dialogDeleteQuestion = true;
    },

    async deleteQuestion() {
      try {
        await this.$services.perspective.deletePerspective(
          this.projectId,
          this.deletingQuestion.id
        );

        this.dialogDeleteQuestion = false;
        await this.fetchPerspectiveGroups();
        
        // Verifica se era a última questão do grupo
        const updatedGroup = this.perspectiveGroups.find(g => g.id === this.currentGroup.id);
        if (updatedGroup && updatedGroup.questions.length === 0) {
          // Abre o diálogo para criar uma nova questão
          this.openAddQuestionDialog(updatedGroup);
          this.snackbarMessage = 'Please add at least one question to the group';
          this.snackbar = true;
        } else {
          this.snackbarMessage = 'Question deleted successfully';
          this.snackbar = true;
        }
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