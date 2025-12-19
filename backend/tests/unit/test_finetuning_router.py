"""
Unit tests for Fine-tuning Router
"""
import pytest
from unittest.mock import Mock, patch, MagicMock
from fastapi import HTTPException
from app.routers.finetuning import router
from app.models import User, FineTuningJob


@pytest.mark.unit
class TestFinetuningRouter:
    """Test suite for Fine-tuning Router"""
    
    def test_create_finetuning_job_success(
        self, client, auth_headers, test_user, db_session
    ):
        """Test creating a fine-tuning job successfully"""
        training_data = {
            "examples": [
                {
                    "question": "Qu'est-ce que l'IA?",
                    "context": "L'IA est l'intelligence artificielle.",
                    "answer": "L'intelligence artificielle"
                }
            ]
        }
        
        response = client.post(
            "/api/finetuning/",
            headers=auth_headers,
            json={
                "job_name": "Test QA Model",
                "model_type": "qa",
                "training_data": training_data
            }
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "id" in data
        assert data["job_name"] == "Test QA Model"
        assert data["model_type"] == "qa"
        assert data["status"] == "pending"
    
    def test_create_finetuning_job_invalid_model_type(
        self, client, auth_headers
    ):
        """Test creating job with invalid model type"""
        training_data = {"examples": []}
        
        response = client.post(
            "/api/finetuning/",
            headers=auth_headers,
            json={
                "job_name": "Test",
                "model_type": "invalid",
                "training_data": training_data
            }
        )
        
        assert response.status_code == 400
    
    def test_create_finetuning_job_invalid_training_data(
        self, client, auth_headers
    ):
        """Test creating job with invalid training data"""
        response = client.post(
            "/api/finetuning/",
            headers=auth_headers,
            json={
                "job_name": "Test",
                "model_type": "qa",
                "training_data": {}
            }
        )
        
        assert response.status_code == 400
    
    def test_list_finetuning_jobs(
        self, client, auth_headers, test_user, db_session
    ):
        """Test listing fine-tuning jobs"""
        # Create a test job
        job = FineTuningJob(
            user_id=test_user.id,
            job_name="Test Job",
            model_type="qa",
            training_data='{"examples": []}',
            status="pending"
        )
        db_session.add(job)
        db_session.commit()
        
        response = client.get(
            "/api/finetuning/",
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) >= 1
    
    def test_get_finetuning_job(
        self, client, auth_headers, test_user, db_session
    ):
        """Test getting a specific fine-tuning job"""
        job = FineTuningJob(
            user_id=test_user.id,
            job_name="Test Job",
            model_type="qa",
            training_data='{"examples": []}',
            status="completed"
        )
        db_session.add(job)
        db_session.commit()
        
        response = client.get(
            f"/api/finetuning/{job.id}",
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == job.id
        assert data["job_name"] == "Test Job"
    
    def test_get_finetuning_job_not_found(self, client, auth_headers):
        """Test getting non-existent job"""
        response = client.get(
            "/api/finetuning/99999",
            headers=auth_headers
        )
        
        assert response.status_code == 404
    
    @patch('app.routers.finetuning.os.path.exists')
    @patch('shutil.rmtree')
    def test_delete_finetuning_job(
        self, mock_rmtree, mock_exists,
        client, auth_headers, test_user, db_session
    ):
        """Test deleting a fine-tuning job"""
        mock_exists.return_value = True
        
        job = FineTuningJob(
            user_id=test_user.id,
            job_name="Test Job",
            model_type="qa",
            training_data='{"examples": []}',
            status="completed",
            model_path="./test_path"
        )
        db_session.add(job)
        db_session.commit()
        
        response = client.delete(
            f"/api/finetuning/{job.id}",
            headers=auth_headers
        )
        
        assert response.status_code == 200
        assert "message" in response.json()

