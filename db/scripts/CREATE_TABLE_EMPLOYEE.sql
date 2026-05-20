SET FEEDBACK ON
SET SERVEROUTPUT ON
BEGIN
    EXECUTE IMMEDIATE '
        CREATE TABLE EMPLOYEE (
            emp_id     NUMBER PRIMARY KEY,
            emp_name   VARCHAR2(100),
            emp_dept   VARCHAR2(50),
            hire_date  DATE DEFAULT SYSDATE
        )';
EXCEPTION
    WHEN OTHERS THEN
        IF SQLCODE = -955 THEN
            DBMS_OUTPUT.PUT_LINE('TABLE EMPLOYEE already exists. Skipping.');
        ELSE
            RAISE;
        END IF;
END;
/
EXIT;
