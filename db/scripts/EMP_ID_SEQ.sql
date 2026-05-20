CREATE OR REPLACE PROCEDURE EMP_ID_SEQ IS
    v_exists NUMBER := 0;
BEGIN
    SELECT COUNT(*) INTO v_exists FROM user_sequences WHERE sequence_name = 'EMP_ID_SEQ';
    IF v_exists = 0 THEN
EXECUTE IMMEDIATE q'[
CREATE SEQUENCE emp_id_seq
    START WITH 1
    INCREMENT BY 1
    NOCACHE
    NOCYCLE;
	 ]';
    ELSE
        DBMS_OUTPUT.PUT_LINE('TABLE emp_id_seq already exists. Skipping creation.');
    END IF;
EXCEPTION WHEN OTHERS THEN
    DBMS_OUTPUT.PUT_LINE('Error creating TABLE emp_id_seq: ' || SQLERRM);
END;
/
