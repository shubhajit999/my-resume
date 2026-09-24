import pytest
from sqlalchemy import create_engine, select
from sqlalchemy.orm import sessionmaker

from app.core.config import settings
from app.db.base import Base
from app.models.user import User
from app.models.resume import Resume
from app.models.sections import PersonalInfo, WorkExperience


@pytest.fixture
def test_db_session():
    """
    Creates an isolated test database session for Phase 1 DB tests.
    """
    connect_args = {"check_same_thread": False} if settings.TEST_DATABASE_URL.startswith("sqlite") else {}
    test_engine = create_engine(settings.TEST_DATABASE_URL, connect_args=connect_args)
    
    # Create all tables on test DB
    Base.metadata.create_all(bind=test_engine)
    
    TestSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)
    session = TestSessionLocal()
    
    try:
        yield session
    finally:
        session.close()
        # Drop all tables after test completion
        Base.metadata.drop_all(bind=test_engine)


def test_database_connection(test_db_session):
    """
    Verifies test database connection and basic query execution.
    """
    result = test_db_session.execute(select(1)).scalar()
    assert result == 1


def test_models_creation_and_cascade_delete(test_db_session):
    """
    Verifies creation of User, Resume, and nested sections with CASCADE deletion.
    """
    # Create User
    user = User(
        email="testuser@example.com",
        hashed_password="securehashedpassword",
        full_name="Test User",
    )
    test_db_session.add(user)
    test_db_session.commit()
    test_db_session.refresh(user)

    assert user.id is not None

    # Create Resume for User
    resume = Resume(
        user_id=user.id,
        title="Software Engineer Resume",
        template_id="modern",
        theme_config={"primary_color": "#007bff", "section_order": ["personal", "experience"]},
    )
    test_db_session.add(resume)
    test_db_session.commit()
    test_db_session.refresh(resume)

    assert resume.id is not None
    assert resume.user_id == user.id

    # Add PersonalInfo section
    personal_info = PersonalInfo(
        resume_id=resume.id,
        full_name="Test User",
        email="testuser@example.com",
        summary="Experienced Developer",
    )
    test_db_session.add(personal_info)

    # Add WorkExperience section
    work_exp = WorkExperience(
        resume_id=resume.id,
        company="Tech Corp",
        position="Senior Developer",
        is_current=True,
        display_order=0,
    )
    test_db_session.add(work_exp)
    test_db_session.commit()

    # Query resume with relationships
    queried_resume = test_db_session.execute(
        select(Resume).where(Resume.id == resume.id)
    ).scalar_one()

    assert queried_resume.personal_info.summary == "Experienced Developer"
    assert len(queried_resume.work_experiences) == 1
    assert queried_resume.work_experiences[0].company == "Tech Corp"

    # Test Cascade Delete
    test_db_session.delete(user)
    test_db_session.commit()

    deleted_resume = test_db_session.execute(
        select(Resume).where(Resume.id == resume.id)
    ).scalar_one_or_none()
    assert deleted_resume is None
