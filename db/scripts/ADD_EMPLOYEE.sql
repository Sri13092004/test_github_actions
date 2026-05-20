SET SERVEROUTPUT ON;
create or replace PROCEDURE add_employee (
    p_emp_name IN VARCHAR2,
    p_emp_dept IN VARCHAR2
) AS
BEGIN
    INSERT INTO employee (emp_id, emp_name, emp_dept)
    VALUES (emp_id_seq.NEXTVAL, p_emp_name, p_emp_dept);

    COMMIT;
END;
/
EXIT;
