<template>
  <v-card>
    <!-- Error message as pop-up central superior -->
    <transition name="fade">
      <div v-if="errorMessage" class="error-message">
        <v-icon small class="mr-2" color="error">mdi-alert-circle</v-icon>
        {{ errorMessage }}
      </div>
    </transition>

    <v-card-title v-if="isProjectAdmin">
      <action-menu
        @upload="$router.push('dataset/import')"
        @download="$router.push('dataset/export')"
        @assign="dialogAssignment = true"
        @reset="dialogReset = true"
        @compare="dialogCompareForm = true"
      />
      <v-btn
        class="text-capitalize ms-2"
        color="error"
        outlined
        @click="updateProjectStatus('closed')"
      >
        Fechar Projeto
      </v-btn>
      <v-btn
        class="text-capitalize ms-2"
        color="success"
        outlined
        @click="updateProjectStatus('open')"
      >
        Reabrir Projeto
      </v-btn>
      <v-btn
        class="text-capitalize ms-2"
        :disabled="!canDelete"
        outlined
        @click.stop="dialogDelete = true"
      >
        Delete
      </v-btn>
      <v-spacer />
      <v-btn
        :disabled="!item.count"
        class="text-capitalize"
        color="error"
        @click="dialogDeleteAll = true"
      >
        Delete All
      </v-btn>
      <v-dialog v-model="dialogDelete">
        <form-delete
          :selected="selected"
          :item-key="itemKey"
          @cancel="dialogDelete = false"
          @remove="remove"
        />
      </v-dialog>
      <v-dialog v-model="dialogDeleteAll">
        <form-delete-bulk @cancel="dialogDeleteAll = false" @remove="removeAll" />
      </v-dialog>
      <v-dialog v-model="dialogAssignment">
        <form-assignment @assigned="assigned" @cancel="dialogAssignment = false" />
      </v-dialog>
      <v-dialog v-model="dialogReset">
        <form-reset-assignment @cancel="dialogReset = false" @reset="resetAssignment" />
      </v-dialog>
      <v-dialog v-model="dialogCompareForm" max-width="500">
        <form-compare-annotations
          :project-id="projectId"
          :documents="item.items"
          :project-users="projectUsers"
          @cancel="dialogCompareForm = false"
          @compare="openComparisonDialog"
          @error="handleCompareError"
        />
      </v-dialog>
    </v-card-title>
    
    <image-list
      v-if="project.isImageProject"
      v-model="selected"
      :items="item.items"
      :is-admin="user.isProjectAdmin"
      :is-loading="isLoading"
      :members="members"
      :total="item.count"
      @update:query="updateQuery"
      @click:labeling="movePage"
      @assign="assign"
      @unassign="unassign"
    />
    <audio-list
      v-else-if="project.isAudioProject"
      v-model="selected"
      :items="item.items"
      :is-admin="user.isProjectAdmin"
      :is-loading="isLoading"
      :members="members"
      :total="item.count"
      @update:query="updateQuery"
      @click:labeling="movePage"
      @assign="assign"
      @unassign="unassign"
    />
    <document-list
      v-else
      v-model="selected"
      :items="item.items"
      :is-admin="user.isProjectAdmin"
      :is-loading="isLoading"
      :members="members"
      :total="item.count"
      @update:query="updateQuery"
      @click:labeling="movePage"
      @edit="editItem"
      @vote="openVotePage"
      @assign="assign"
      @unassign="unassign"
    />
<v-dialog v-model="dialogCompare" max-width="90%" height="80vh" content-class="comparison-dialog">
      <v-card class="comparison-card">
        <v-toolbar dark color="primary" dense>
          <v-btn icon @click="dialogCompare = false">
            <v-icon>mdi-close</v-icon>
          </v-btn>
          <v-toolbar-title>Annotation Comparison</v-toolbar-title>
          <v-spacer></v-spacer>
          <v-chip small class="mr-2">
            <v-avatar left>
              <v-icon x-small>mdi-file-document</v-icon>
            </v-avatar>
            Document #{{ selectedDocumentId }}
          </v-chip>
        </v-toolbar>
        
        <!-- Comparison component -->
        <comparison-view
          v-if="dialogCompare"
          :project-id="projectId"
          :document-id="selectedDocumentId"
          :user1-id="comparisonUsers.user1"
          :user2-id="comparisonUsers.user2"
          :labels="project && project.labels ? project.labels : []"
          :users="projectUsers || []"
          @close="dialogCompare = false"
          @no-annotations="handleNoAnnotations"
        />
      </v-card>
    </v-dialog>

    <!-- Add this for showing no annotations message -->
    <v-snackbar
      v-model="noAnnotationsSnackbar"
      :timeout="5000"
      color="warning"
    >
      {{ noAnnotationsMessage }}
      <template #action="{ attrs }">
        <v-btn
          text
          v-bind="attrs"
          @click="noAnnotationsSnackbar = false"
        >
          Close
        </v-btn>
      </template>
    </v-snackbar>
  </v-card>
</template>

<script lang="ts">
import _ from 'lodash'
import { mapGetters } from 'vuex'
import Vue from 'vue'
import { NuxtAppOptions } from '@nuxt/types'
import DocumentList from '@/components/example/DocumentList.vue'
import FormAssignment from '~/components/example/FormAssignment.vue'
import FormDelete from '@/components/example/FormDelete.vue'
import FormDeleteBulk from '~/components/example/FormDeleteBulk.vue'
import FormResetAssignment from '~/components/example/FormResetAssignment.vue'
import ActionMenu from '~/components/example/ActionMenu.vue'
import AudioList from '~/components/example/AudioList.vue'
import ImageList from '~/components/example/ImageList.vue'
import { getLinkToAnnotationPage } from '~/presenter/linkToAnnotationPage'
import { ExampleDTO, ExampleListDTO } from '~/services/application/example/exampleData'
import { MemberItem } from '~/domain/models/member/member'
import ComparisonView from '~/components/annotations/ComparisonView.vue'
import FormCompareAnnotations from '~/components/example/FormCompareAnnotations.vue'

export default Vue.extend({
  components: {
    ActionMenu,
    AudioList,
    DocumentList,
    ImageList,
    FormAssignment,
    FormDelete,
    FormDeleteBulk,
    FormResetAssignment,
    FormCompareAnnotations,
    ComparisonView
  },

  layout: 'project',

  middleware: ['check-auth', 'auth', 'setCurrentProject'],

  validate({ params, query }: NuxtAppOptions) {
    return /^\d+$/.test(params.id) && /^\d+|$/.test(query.limit) && /^\d+|$/.test(query.offset)
  },

  data() {
    return {
      dialogDelete: false,
      dialogDeleteAll: false,
      dialogAssignment: false,
      dialogReset: false,
      dialogCompare: false,
      dialogCompareForm: false,
      item: {} as ExampleListDTO,
      selected: [] as ExampleDTO[],
      members: [] as MemberItem[],
      user: {} as MemberItem,
      isLoading: false,
      isProjectAdmin: false,
      selectedDocumentId: null,
      comparisonUsers: {
        user1: null,
        user2: null
      },
      projectUsers: [] as MemberItem[],
      noAnnotationsSnackbar: false,
      noAnnotationsMessage: '',
      dialogEdit: false,
      editedItem: {} as ExampleDTO,
      page: 1,

      search: '', // Initialize search property

      errorMessage: '',
      hasError: false,

    }
  },

  async fetch(this: NuxtAppOptions) {
    this.isLoading = true
    this.item = await this.$services.example.list(this.projectId, this.$route.query)
    this.user = await this.$repositories.member.fetchMyRole(this.projectId)
    
    // Only load members if user is admin
    if (this.user.isProjectAdmin) {
      try {
        this.members = await this.$repositories.member.list(this.projectId)
      } catch (error) {
        console.warn('Could not load project members:', error)
        this.members = []
      }
    } else {
      // For regular users, only include themselves
      this.members = [this.user]
    }
    
    this.isLoading = false
  },

  computed: {
    ...mapGetters('projects', ['project']),

    canDelete(): boolean {
      return this.selected.length > 0
    },

    projectId(): string {
      return this.$route.params.id
    },

    itemKey(): string {
      if (this.project.isImageProject || this.project.isAudioProject) {
        return 'filename'
      } else {
        return 'text'
      }
    },
  },

  watch: {
    '$route.query': _.debounce(function () {
      this.$fetch()
    }, 1000),
    
    errorMessage(newVal) {
      if (newVal) {
        this.dialogCompare = false;
        this.dialogCompareForm = false;
      }
    },
    
    hasError(newVal) {
      if (newVal) {
        this.dialogCompare = false;
        this.dialogCompareForm = false;
      }
    }
  },

  async created() {
    const member = await this.$repositories.member.fetchMyRole(this.projectId)
    this.isProjectAdmin = member.isProjectAdmin
    
    // Only load project members if user is an admin
    if (this.isProjectAdmin) {
      try {
        this.projectUsers = await this.$repositories.member.list(this.projectId)
      } catch (error) {
        console.warn('Could not load project members:', error)
        this.projectUsers = []
      }
    } else {
      // For regular users, only include themselves
      this.projectUsers = [member]
    }
  },

  methods: {
    async remove() {
      await this.$services.example.bulkDelete(this.projectId, this.selected)
      await this.$fetch()
      this.dialogDelete = false
      this.selected = []
    },

    async removeAll() {
      await this.$services.example.bulkDelete(this.projectId, [])
      this.$fetch()
      this.dialogDeleteAll = false
      this.selected = []
    },

    updateQuery(query: object) {
      this.$router.push(query)
    },

    movePage(query: object) {
      const link = getLinkToAnnotationPage(this.projectId, this.project.projectType)
      this.updateQuery({
        path: this.localePath(link),
        query
      })
    },

    editItem(item: ExampleDTO) {
      this.editedItem = Object.assign({}, item)
      this.dialogEdit = true
    },

    async assign(exampleId: number, assigneeId: number) {
      try {
        await this.$repositories.assignment.assign(this.projectId, exampleId, assigneeId);
        await this.$fetch(); // Refresh data to reflect changes
      } catch (error) {
        console.error('Error assigning member:', error);
        this.$toasted.error('Failed to assign member.');
      }
    },

    async unassign(assignmentId: string) {
      try {
        await this.$repositories.assignment.unassign(this.projectId, assignmentId);
        await this.$fetch(); // Refresh data to reflect changes
      } catch (error) {
        console.error('Error unassigning member:', error);
        this.$toasted.error('Failed to unassign member.');
      }
    },

    async assigned() {
      this.dialogAssignment = false
      this.item = await this.$services.example.list(this.projectId, this.$route.query)
    },

    async resetAssignment() {
      this.dialogReset = false
      await this.$repositories.assignment.reset(this.projectId)
      this.item = await this.$services.example.list(this.projectId, this.$route.query)
    },


    openComparisonDialog(this: NuxtAppOptions, 
      users: { user1: number; user2: number; documentId: number }) {
      if (this.errorMessage || this.hasError) {
        this.dialogCompare = false;
        return;
      }
      

      this.selectedDocumentId = users.documentId;
      this.comparisonUsers.user1 = users.user1;
      this.comparisonUsers.user2 = users.user2;
      this.dialogCompareForm = false;
      this.dialogCompare = true;
    },


    handleNoAnnotations(event) {
      if (!event.response || (event.response.status && event.response.status >= 500)) {
        this.errorMessage = 'Database unavailable at the moment, please try again later.';
        setTimeout(() => { this.errorMessage = ''; }, 5000);
      } else {
        this.noAnnotationsMessage = event.message;
        this.noAnnotationsSnackbar = true;
      }

    },

    openVotePage(item: ExampleDTO) {
      const link = getLinkToAnnotationPage(this.projectId, this.project.projectType);
      this.$router.push({
        path: this.localePath(link),
        query: {
          exampleId: item.id,
          q: this.search,
          page: String(this.page),
          activeTab: 'vote'
        }
      })
    },

    async updateExample() {
      try {
        await this.$services.example.update(this.projectId, this.editedItem)
        this.dialogEdit = false
        await this.$fetch()
      } catch (e) {
        console.log(e)
      }
    },

    async updateProjectStatus(newStatus: string) {
      try {
        await this.$repositories.project.update(this.projectId, { status: newStatus });
        await this.$store.dispatch('projects/fetchProject', this.projectId);
        
        // If closing project, navigate to projects list
        if (newStatus === 'closed') {
          this.$router.push('/projects');
          this.$toasted.success('Projeto fechado!');
        } else {
          // If opening project, navigate to the project's dataset page
          this.$router.push(`/projects/${this.projectId}/dataset`);
          this.$toasted.success('Projeto reaberto!');
        }
        
        this.$forceUpdate();
      } catch (e) {
        this.$toasted.error('Erro ao atualizar status do projeto.');
      }
    },
    async toggleProjectStatus() {
      const currentStatus = this.project.status;
      const newStatus = currentStatus === 'open' ? 'closed' : 'open';
      await this.updateProjectStatus(newStatus);
    },

    handleCompareError(errorMessage: string) {
      this.errorMessage = errorMessage;
      this.hasError = true;
      this.dialogCompareForm = false;
      this.dialogCompare = false;
    }
  }
})
</script>

<style scoped>
/* Style for the comparison dialog */
::v-deep .comparison-dialog {
  margin: 24px;
  height: calc(100vh - 48px) !important;
  max-height: calc(100vh - 48px) !important;
  display: flex;
  justify-content: center;
}

::v-deep .comparison-card {
  height: 100%;
  display: flex;
  flex-direction: column;
  width: 100%;
  max-width: 1200px;
  margin: 0 auto;
}

/* Add a subtle shadow to make it feel like a floating card */
::v-deep .v-card.comparison-card {
  box-shadow: 0 8px 36px rgba(0, 0, 0, 0.2) !important;
}

/* Keep your existing styles for non-fullscreen dialogs */
::v-deep .v-dialog:not(.v-dialog--fullscreen) {
  width: 800px;
}

.error-message {
  position: fixed;
  top: 20px;
  left: 50%;
  transform: translateX(-50%);
  z-index: 2000;
  background-color: #fdecea;
  color: #b71c1c;
  padding: 12px 24px;
  border-radius: 8px;
  display: flex;
  align-items: center;
  font-weight: 500;
  box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
  pointer-events: none;
}

.fade-enter-active,
.fade-leave-active {
  transition: opacity 0.4s ease;
}

.fade-enter,
.fade-leave-to {
  opacity: 0;
}
</style>
