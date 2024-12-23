from flask import Flask, render_template, request, redirect, url_for, flash
import json
from datetime import datetime, date
from pathlib import Path

app = Flask(__name__)
app.secret_key = 'your-secret-key-here'  # Required for flash messages

# Ensure the data directory exists
Path("data").mkdir(exist_ok=True)

class ProjectManager:
    def __init__(self):
        self.projects = {}
        self.data_file = Path("data/projects.json")
        self.load_data()

    def save_data(self):
        with open(self.data_file, 'w') as f:
            json.dump(self.projects, f, indent=2)

    def load_data(self):
        try:
            with open(self.data_file, 'r') as f:
                self.projects = json.load(f)
        except FileNotFoundError:
            self.projects = {}

    def add_project(self, name, description, project_type="regular"):
        if name not in self.projects:
            self.projects[name] = {
                'description': description,
                'type': project_type,
                'tasks': [],
                'created_at': datetime.now().isoformat(),
                'status': 'active',
                'tags': [],
                'time_estimate': None,
                'time_spent': 0
            }
            self.save_data()
            return True
        return False

    def quick_add_idea(self, name):
        return self.add_project(name, "", project_type="idea")

pm = ProjectManager()

@app.route('/')
def index():
    # Get tag filter from query parameters
    filter_tag = request.args.get('tag')
    
    # Filter projects based on status and tag
    active_projects = {k: v for k, v in pm.projects.items() 
                      if v['status'] == 'active' and 
                      (not filter_tag or filter_tag in v.get('tags', []))}
    
    idea_projects = {k: v for k, v in pm.projects.items() 
                    if v['type'] == 'idea' and 
                    (not filter_tag or filter_tag in v.get('tags', []))}
    
    projects = {
        'active': active_projects,
        'ideas': idea_projects
    }
    return render_template('index.html', projects=projects)

@app.route('/projects')
def projects():
    # Get tag filter from query parameters
    filter_tag = request.args.get('tag')
    
    # Filter projects based on tag
    filtered_projects = {k: v for k, v in pm.projects.items() 
                        if not filter_tag or filter_tag in v.get('tags', [])}
    
    return render_template('projects.html', projects=filtered_projects)
@app.route('/add_project', methods=['POST'])
def add_project():
    name = request.form.get('name')
    description = request.form.get('description', '')
    tags = [tag.strip() for tag in request.form.get('tags', '').split(',') if tag.strip()]
    
    if pm.add_project(name, description):
        # Add tags to the newly created project
        pm.projects[name]['tags'] = tags
        pm.save_data()
        flash('Project added successfully!', 'success')
    else:
        flash('A project with this name already exists.', 'error')
    
    return redirect(url_for('index'))

@app.route('/quick_idea', methods=['POST'])
def quick_idea():
    name = request.form.get('idea_name')
    
    if pm.quick_add_idea(name):
        flash('Idea captured successfully!', 'success')
    else:
        flash('An idea with this name already exists.', 'error')
    
    return redirect(url_for('index'))

@app.route('/view_project/<name>')
def view_project(name):
    if name in pm.projects:
        today = date.today().isoformat()
        return render_template('project.html', name=name, project=pm.projects[name], today=today)
    return redirect(url_for('index'))

@app.route('/edit_project/<name>', methods=['POST'])
def edit_project(name):
    if name in pm.projects:
        new_name = request.form.get('name')
        new_description = request.form.get('description', '')
        new_status = request.form.get('status', 'active')
        new_tags = [tag.strip() for tag in request.form.get('tags', '').split(',') if tag.strip()]

        # If name is changed, check if the new name already exists
        if new_name != name and new_name in pm.projects:
            flash('A project with this name already exists.', 'error')
            return redirect(url_for('view_project', name=name))

        # Store the project data
        project_data = pm.projects[name]
        
        # Update the project data
        project_data['description'] = new_description
        project_data['status'] = new_status
        project_data['tags'] = new_tags

        # If name has changed, update the dictionary key
        if new_name != name:
            pm.projects[new_name] = project_data
            del pm.projects[name]
            name = new_name

        pm.save_data()
        flash('Project updated successfully!', 'success')
        return redirect(url_for('view_project', name=name))
    
    return redirect(url_for('index'))

@app.route('/add_task/<project_name>', methods=['POST'])
def add_task(project_name):
    if project_name in pm.projects:
        task_description = request.form.get('task_description')
        priority = request.form.get('priority', 'medium')
        due_date = request.form.get('due_date')
        
        if task_description:
            pm.projects[project_name]['tasks'].append({
                'description': task_description,
                'completed': False,
                'created_at': datetime.now().isoformat(),
                'priority': priority,
                'priority_order': {'high': 3, 'medium': 2, 'low': 1}[priority],
                'due_date': due_date if due_date else None
            })
            pm.save_data()
            flash('Task added successfully!', 'success')
        else:
            flash('Task description is required!', 'error')
    return redirect(url_for('view_project', name=project_name))

@app.route('/toggle_task/<project_name>/<int:task_index>')
def toggle_task(project_name, task_index):
    if project_name in pm.projects:
        tasks = pm.projects[project_name]['tasks']
        if 0 <= task_index < len(tasks):
            tasks[task_index]['completed'] = not tasks[task_index]['completed']
            pm.save_data()
    return redirect(url_for('view_project', name=project_name))

if __name__ == '__main__':
    app.run(debug=True)