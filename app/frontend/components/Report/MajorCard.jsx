import React from 'react';

const MajorCard = ({ major }) => {
  return (
    <div className="major-card">
      <div className="major-header">
        <h3>{major.major_name}</h3>
        <span className="score">{major.match_score}% Match</span>
      </div>
      <p className="reason"><strong>Tại sao lại hợp:</strong> {major.match_reason}</p>
      <div className="student-life">
        <strong>Sinh viên ngành này làm gì:</strong>
        <p>{major.what_students_do}</p>
      </div>
    </div>
  );
};

export default MajorCard;